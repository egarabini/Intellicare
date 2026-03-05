"""
Restricted Python Sandbox for IntelliCare Bots.
Provides a secure environment to execute arbitrary patient/admin defined python scripts.
"""

from RestrictedPython import compile_restricted, safe_globals, safe_builtins
from RestrictedPython.PrintCollector import PrintCollector
import multiprocessing
import queue
import time

ALLOWED_IMPORTS = {
    "json", "datetime", "math", "re", "hashlib",
    "collections", "itertools", "functools", "typing", "base64", "uuid"
}

def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Import wrapper that only allows whitelisted stdlib modules."""
    if name not in ALLOWED_IMPORTS:
        raise ImportError(f"Import {name} is restricted in this sandbox.")
    return __import__(name, globals, locals, fromlist, level)

def _execute_code(code: str, restricted_globals: dict, result_queue: multiprocessing.Queue):
    """Executes the code and puts the result or error into a queue."""
    try:
        compiled = compile_restricted(code, '<bot>', 'exec')
        # Execute the compiled code in the restricted globals namespace
        # (Updates restricted_globals in place with any variables the script defined)
        exec(compiled, restricted_globals)
        
        # If the script used print(), retrieve its output
        printed_output = ""
        if '_print' in restricted_globals:
            printed_output = restricted_globals['_print']()
            
        result_queue.put({"success": True, "error": None, "printed": printed_output})
    except Exception as e:
        result_queue.put({"success": False, "error": str(e), "printed": ""})

class BotSandbox:
    """Provides a safe sandbox to execute Bot Python code."""

    def __init__(self):
        pass

    def execute(self, code: str, context: 'BotExecutionContext', timeout: int = 30) -> dict: # type: ignore
        """
        Executes python code matching the provided Bot context.
        Enforces a hard timeout to prevent endless loops.
        """
        # Required restricted python components
        restricted_globals = {
            **safe_globals,
            '_print_': PrintCollector,
            '_getattr_': getattr,
            '__builtins__': {
                **safe_builtins, 
                '__import__': _restricted_import,
                'input': context.input_resource, # allow `input()` to return resource 
            },
            'resource': context.input_resource,
            'client': context.fhir_client,
            'secrets': context.secrets,
            'event': context.event_metadata,
            'log': context.logger.info, # standard safe logger since print is captured by _print_
        }

        # Use multiprocessing to safely enforce strict timeouts 
        # (since threading cannot stop CPU-bound infinite loops like while True)
        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=_execute_code, 
            args=(code, restricted_globals, result_queue)
        )
        
        start_time = time.time()
        process.start()
        process.join(timeout=timeout)
        
        duration_ms = int((time.time() - start_time) * 1000)

        if process.is_alive():
            # Code exceeded timeout
            process.terminate()
            process.join()
            return {
                "success": False,
                "error": f"Bot execution exceeded timeout of {timeout}s",
                "duration_ms": duration_ms
            }

        try:
            result = result_queue.get_nowait()
            if result.get("printed"):
                context.logger.info(result["printed"])
                
            return {
                "success": result["success"],
                "error": result["error"],
                "duration_ms": duration_ms
            }
        except queue.Empty:
            return {
                "success": False,
                "error": "Bot process crashed unexpectedly",
                "duration_ms": duration_ms
            }
