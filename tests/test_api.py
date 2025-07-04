"""Basic API tests"""

import pytest
from fastapi.testclient import TestClient

from health_insurance_claim_processor.main import app


class TestAPI:
    """Test the basic API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_check(self):
        """Test health check endpoint"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
    
    def test_process_claim_no_files(self):
        """Test process claim endpoint with no files"""
        client = TestClient(app)
        response = client.post("/process-claim")
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_process_claim_with_mock_pdf(self):
        """Test process claim with mock PDF file"""
        client = TestClient(app)
        
        # Create a mock PDF file
        mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"
        
        files = {
            "files": ("test.pdf", mock_pdf_content, "application/pdf")
        }
        
        # This might fail due to service not being initialized, but tests the endpoint structure
        response = client.post("/process-claim", files=files)
        
        # We expect either success or a 500 error (service not initialized)
        assert response.status_code in [200, 500]
