import pytest
import asyncio
from integrations.mosip_client import (
    MosipClient, MosipConfig, PreRegistrationRequest,
    RegistrationRequest, BiometricCapture
)


class TestMosipClient:
    @pytest.fixture
    def mosip_config(self):
        return MosipConfig(
            base_url="http://localhost:7000",
            client_id="test-client",
            secret="test-secret",
            mode="mock"
        )
    
    @pytest.fixture
    def mosip_client(self, mosip_config):
        return MosipClient(mosip_config)
    
    @pytest.mark.asyncio
    async def test_authentication(self, mosip_client):
        token = await mosip_client.authenticate()
        assert token is not None
        assert mosip_client.auth_token is not None
    
    @pytest.mark.asyncio
    async def test_pre_registration(self, mosip_client):
        await mosip_client.authenticate()
        
        pre_reg_data = PreRegistrationRequest(
            firstName="John",
            lastName="Doe",
            dateOfBirth="1990-01-01",
            gender="Male",
            phone="1234567890",
            addressLine1="123 Test St",
            city="Test City",
            postalCode="12345"
        )
        
        result = await mosip_client.pre_register(pre_reg_data)
        
        assert result['success'] is True
        assert 'preRegId' in result
        assert result['status'] == 'PENDING'
    
    @pytest.mark.asyncio
    async def test_registration(self, mosip_client):
        await mosip_client.authenticate()
        
        reg_data = RegistrationRequest(
            biometricData={},
            demographicData={"name": "John Doe"},
            deviceInfo={"type": "test"}
        )
        
        result = await mosip_client.register(reg_data)
        
        assert result['success'] is True
        assert 'registrationId' in result