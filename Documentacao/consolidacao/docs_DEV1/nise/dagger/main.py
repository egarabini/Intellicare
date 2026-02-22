"""
============================================================================
NISE TRAINING MODULE - DAGGER CI/CD PIPELINE
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Dagger CI/CD Pipeline
Versão: 1.0
Data: 13/03/2026
Responsável: DEV2
============================================================================
"""

import dagger
from dagger import dag, function, object_type
import sys

# ============================================================================
# NISE DAGGER MODULE
# ============================================================================

@object_type
class Nise:
    """Dagger module for NISE Training Module CI/CD"""
    
    @function
    async def test(self, source: dagger.Directory) -> str:
        """
        Run tests for NISE backend.
        
        Args:
            source: Source code directory
        
        Returns:
            str: Test results
        """
        return await (
            dag.container()
            .from_("python:3.11-slim")
            .with_directory("/src", source)
            .with_workdir("/src/backend")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
            .with_exec(["pip", "install", "pytest", "pytest-asyncio", "pytest-cov"])
            .with_exec(["pytest", "-v", "--cov=app", "--cov-report=term"])
            .stdout()
        )
    
    @function
    async def lint(self, source: dagger.Directory) -> str:
        """
        Run linting for NISE backend.
        
        Args:
            source: Source code directory
        
        Returns:
            str: Lint results
        """
        return await (
            dag.container()
            .from_("python:3.11-slim")
            .with_directory("/src", source)
            .with_workdir("/src/backend")
            .with_exec(["pip", "install", "ruff", "black", "mypy"])
            .with_exec(["ruff", "check", "app/"])
            .with_exec(["black", "--check", "app/"])
            .stdout()
        )
    
    @function
    async def build_image(
        self, 
        source: dagger.Directory,
        tag: str = "latest"
    ) -> dagger.Container:
        """
        Build Docker image for NISE backend.
        
        Args:
            source: Source code directory
            tag: Image tag
        
        Returns:
            Container: Built container
        """
        return (
            dag.container()
            .from_("python:3.11-slim")
            .with_directory("/app", source.directory("backend"))
            .with_workdir("/app")
            .with_exec(["pip", "install", "--no-cache-dir", "-r", "requirements.txt"])
            .with_entrypoint(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])
            .with_exposed_port(8000)
        )
    
    @function
    async def publish_image(
        self,
        source: dagger.Directory,
        registry: str,
        username: str,
        password: dagger.Secret,
        tag: str = "latest"
    ) -> str:
        """
        Build and publish Docker image to registry.
        
        Args:
            source: Source code directory
            registry: Container registry URL
            username: Registry username
            password: Registry password (secret)
            tag: Image tag
        
        Returns:
            str: Published image reference
        """
        container = await self.build_image(source, tag)
        
        image_ref = f"{registry}/nise-backend:{tag}"
        
        await (
            container
            .with_registry_auth(registry, username, password)
            .publish(image_ref)
        )
        
        return image_ref
    
    @function
    async def deploy_dev(
        self,
        source: dagger.Directory,
        db_host: str,
        db_password: dagger.Secret
    ) -> str:
        """
        Deploy NISE to development environment.
        
        Args:
            source: Source code directory
            db_host: Database host
            db_password: Database password (secret)
        
        Returns:
            str: Deployment status
        """
        # Build image
        container = await self.build_image(source, "dev")
        
        # Run migrations
        await (
            dag.container()
            .from_("python:3.11-slim")
            .with_directory("/app", source.directory("backend"))
            .with_workdir("/app")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
            .with_env_variable("DB_HOST", db_host)
            .with_secret_variable("DB_PASSWORD", db_password)
            .with_exec(["python", "scripts/run_migrations.py"])
            .sync()
        )
        
        return "✅ Deployed to development environment"
    
    @function
    async def populate_data(
        self,
        source: dagger.Directory,
        db_host: str,
        db_password: dagger.Secret,
        data_type: str = "all"
    ) -> str:
        """
        Populate synthetic data in database.
        
        Args:
            source: Source code directory
            db_host: Database host
            db_password: Database password (secret)
            data_type: Type of data (patients, observations, practitioners, encounters, all)
        
        Returns:
            str: Population status
        """
        scripts = {
            "patients": "populate_patients.py",
            "observations": "populate_observations.py",
            "practitioners": "populate_practitioners.py",
            "encounters": "populate_encounters.py"
        }
        
        if data_type == "all":
            scripts_to_run = list(scripts.values())
        else:
            scripts_to_run = [scripts.get(data_type, "")]
        
        for script in scripts_to_run:
            if script:
                await (
                    dag.container()
                    .from_("python:3.11-slim")
                    .with_directory("/app", source.directory("backend"))
                    .with_workdir("/app")
                    .with_exec(["pip", "install", "-r", "requirements.txt"])
                    .with_env_variable("DB_HOST", db_host)
                    .with_secret_variable("DB_PASSWORD", db_password)
                    .with_exec(["python", f"scripts/{script}"])
                    .sync()
                )
        
        return f"✅ Populated {data_type} data successfully"

