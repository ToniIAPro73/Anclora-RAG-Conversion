#!/usr/bin/env python3
"""
Script to properly ingest the Pandoc GitHub repository into the RAG system.
This script will:
1. Clone and analyze the Pandoc repository
2. Process the files
3. Upload them through the API to create vector embeddings
"""

import asyncio
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import requests
from datetime import datetime

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from app.ingestion.github_processor import GitHubRepositoryProcessor, RepositoryOptions

class PandocIngestor:
    def __init__(self, api_url: str = "http://localhost:8081", api_token: str | None = None):
        self.api_url = api_url
        self.api_token = api_token or os.getenv("ANCLORA_API_TOKEN", "iFqEvYPHcqfyCQvDV8vPcS0Z10SZDeVJ9ErCAR5uEU4")
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        self.processor = GitHubRepositoryProcessor()

    def test_api_connection(self) -> bool:
        """Test if the API is accessible."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ API connection successful")
                return True
            else:
                print(f"❌ API returned status code: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            return False

    async def clone_and_analyze_pandoc(self) -> Dict[str, Any] | None:
        """Clone and analyze the Pandoc repository."""
        print("🔍 Cloning and analyzing Pandoc repository...")

        pandoc_url = "https://github.com/jgm/pandoc.git"
        options = RepositoryOptions(
            include_docs=True,
            include_code=True,
            max_file_size_mb=10,  # Limit file size for faster processing
            allowed_extensions=[".md", ".txt", ".rst", ".py", ".hs", ".cabal"]  # Focus on documentation and source
        )

        try:
            analysis = await self.processor.analyze_repository(pandoc_url, "main", options)
            if analysis and analysis.get("success"):
                print("✅ Repository analysis successful")
                print(f"   📁 Total files: {analysis['total_files']}")
                print(f"   📏 Total size: {analysis['total_size_mb']} MB")
                print(f"   📂 Temp path: {analysis['temp_path']}")
                return analysis
            else:
                print(f"❌ Repository analysis failed: {analysis.get('error') if analysis else 'Unknown error'}")
                return None
        except Exception as e:
            print(f"❌ Error during repository analysis: {e}")
            return None
    def upload_file_to_api(self, file_path: Path, filename: str) -> bool:
        """Upload a single file through the API."""
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Create a file-like object for the request
            files = {
                'file': (filename, file_content, 'application/octet-stream')
            }

            # Upload to API
            response = requests.post(
                f"{self.api_url}/upload",
                files=files,
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Uploaded: {filename}")
                return True
            else:
                print(f"   ❌ Upload failed for {filename}: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Error uploading {filename}: {e}")
            return False

    async def upload_repository_files(self, repo_path: str, max_files: int = 50) -> int:
        """Upload repository files through the API."""
        print(f"📤 Uploading files to RAG system (max: {max_files})...")

        base_path = Path(repo_path)
        uploaded_count = 0

        # Get all files from the analysis
        options = RepositoryOptions(include_docs=True, include_code=True, max_file_size_mb=5)
        files = await self.processor.gather_repository_files(repo_path, options)

        print(f"   📋 Found {len(files)} files to process")

        # Upload files (limit to max_files for faster testing)
        for i, file_info in enumerate(files[:max_files]):
            file_path = base_path / file_info["relative_path"]

            if file_path.exists() and file_path.is_file():
                print(f"   [{i+1}/{min(len(files), max_files)}] Processing: {file_info['relative_path']}")
                if self.upload_file_to_api(file_path, file_info["relative_path"]):
                    uploaded_count += 1

        return uploaded_count

    def check_indexed_documents(self) -> List[str]:
        """Check what documents are currently indexed."""
        try:
            response = requests.get(
                f"{self.api_url}/documents",
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                documents = result.get("documents", [])
                print(f"📚 Currently indexed documents: {len(documents)}")
                for doc in documents[:10]:  # Show first 10
                    print(f"   • {doc}")
                if len(documents) > 10:
                    print(f"   ... and {len(documents) - 10} more")
                return documents
            else:
                print(f"❌ Failed to get documents: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error checking documents: {e}")
            return []

    def test_pandoc_query(self) -> bool:
        """Test a query about Pandoc to verify ingestion worked."""
        print("🧪 Testing Pandoc query...")

        test_query = "¿Qué me puedes contar acerca de la librería Pandoc?"

        try:
            response = requests.post(
                f"{self.api_url}/chat",
                headers=self.headers,
                json={
                    "message": test_query,
                    "language": "es",
                    "max_length": 1000
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")

                print("✅ Query successful!")
                print(f"📝 Response preview: {response_text[:200]}...")

                # Check if the response contains actual information about Pandoc
                pandoc_keywords = ["pandoc", "conversión", "documentos", "markdown", "formato"]
                has_pandoc_info = any(keyword in response_text.lower() for keyword in pandoc_keywords)

                if has_pandoc_info and "no tengo documentos" not in response_text.lower():
                    print("✅ Response contains Pandoc information - ingestion successful!")
                    return True
                else:
                    print("⚠️ Response doesn't contain specific Pandoc information")
                    return False
            else:
                print(f"❌ Query failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error during query test: {e}")
            return False

    async def run_ingestion(self):
        """Run the complete ingestion process."""
        print("🚀 Starting Pandoc repository ingestion process")
        print("=" * 60)

        # Step 1: Test API connection
        if not self.test_api_connection():
            print("❌ Cannot proceed without API connection")
            return False

        # Step 2: Clone and analyze repository
        analysis = await self.clone_and_analyze_pandoc()
        if not analysis:
            print("❌ Cannot proceed without repository analysis")
            return False

        # Step 3: Upload files
        repo_path = analysis["temp_path"]
        uploaded_count = await self.upload_repository_files(repo_path, max_files=30)

        print(f"\n📊 Upload complete: {uploaded_count} files uploaded")

        # Step 4: Wait a bit for processing
        print("⏳ Waiting for document processing...")
        await asyncio.sleep(10)

        # Step 5: Check indexed documents
        print("\n🔍 Checking indexed documents...")
        documents = self.check_indexed_documents()

        # Step 6: Test query
        print("\n🧪 Testing Pandoc query...")
        query_success = self.test_pandoc_query()

        # Step 7: Cleanup
        if repo_path and os.path.exists(repo_path):
            print(f"\n🧹 Cleaning up temporary repository: {repo_path}")
            shutil.rmtree(repo_path, ignore_errors=True)

        # Final results
        print("\n" + "=" * 60)
        print("📋 INGESTION RESULTS")
        print("=" * 60)
        print(f"✅ Repository analyzed: {analysis['success']}")
        print(f"📁 Files found: {analysis['total_files']}")
        print(f"📤 Files uploaded: {uploaded_count}")
        print(f"📚 Documents indexed: {len(documents)}")
        print(f"🧪 Query test: {'✅ PASSED' if query_success else '❌ FAILED'}")

        return query_success

async def main():
    """Main function."""
    api_token = os.getenv("ANCLORA_API_TOKEN", "iFqEvYPHcqfyCQvDV8vPcS0Z10SZDeVJ9ErCAR5uEU4")

    ingestor = PandocIngestor(api_token=api_token)
    success = await ingestor.run_ingestion()

    if success:
        print("\n🎉 Pandoc repository successfully ingested into RAG system!")
        print("You can now ask questions about Pandoc and get informed responses.")
    else:
        print("\n⚠️ Ingestion completed but query test failed.")
        print("The documents may still be processing or there might be an issue.")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())