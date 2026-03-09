import asyncio
import json
import traceback

async def run_test():
    try:
        from intellicare_auth.smart.router import smart_configuration
        result = await smart_configuration()
        print('JSON:', json.dumps(result, indent=2))
    except Exception as e:
        print("Error occurred:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
