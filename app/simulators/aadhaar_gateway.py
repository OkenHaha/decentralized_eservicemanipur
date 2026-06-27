import datetime

# Mock Aadhaar Registry database for simulation
MOCK_AADHAAR_REGISTRY = {
    "999900000001": {
        "AadhaarNumber": "9999-0000-0001",
        "Name": "Laishram Tomba Singh",
        "FatherName": "Laishram Ibohal Singh",
        "DOB": datetime.date(1995, 3, 15),
        "Gender": "MALE",
        "Address": "Kwakeithel Heinoukhongnembi, Imphal West",
        "Zip": "795001",
        "Mobile": "9876543210"
    },
    "999900000002": {
        "AadhaarNumber": "9999-0000-0002",
        "Name": "Oinam Bembem Devi",
        "FatherName": "Oinam Jugeshwor Singh",
        "DOB": datetime.date(1988, 7, 22),
        "Gender": "FEMALE",
        "Address": "Thoubal Achouba, Thoubal",
        "Zip": "795138",
        "Mobile": "9876543211"
    },
    "999900000003": {
        "AadhaarNumber": "9999-0000-0003",
        "Name": "Naorem Roshibina Chanu",
        "FatherName": "Naorem Priyokumar Singh",
        "DOB": datetime.date(2001, 11, 8),
        "Gender": "FEMALE",
        "Address": "Khuman Lampak, Imphal East",
        "Zip": "795002",
        "Mobile": "9876543212"
    },
    "999900000004": {
        "AadhaarNumber": "9999-0000-0004",
        "Name": "Keisham Ranbir Singh",
        "FatherName": "Keisham Tomchou Singh",
        "DOB": datetime.date(1990, 5, 10),
        "Gender": "MALE",
        "Address": "Sagolband Meino Leirak, Imphal West",
        "Zip": "795001",
        "Mobile": "9876543213"
    },
    "999900000005": {
        "AadhaarNumber": "9999-0000-0005",
        "Name": "Chongtham Sanjoy Singh",
        "FatherName": "Chongtham Kulabidhu Singh",
        "DOB": datetime.date(1997, 12, 5),
        "Gender": "MALE",
        "Address": "Moirang Lamkhai, Bishnupur",
        "Zip": "795133",
        "Mobile": "9876543214"
    }
}

class AadhaarValidationError(Exception):
    pass

def query_central_registry(aadhaar_id: str, mobile: str) -> dict:
    """
    Simulates checking credentials with UIDAI Aadhaar registry.
    """
    # Clean string from hyphens or spaces
    clean_id = str(aadhaar_id).replace("-", "").replace(" ", "")
    
    if clean_id not in MOCK_AADHAAR_REGISTRY:
        raise AadhaarValidationError("AADHAAR_NOT_FOUND: The Aadhaar card number was not found in the national registry.")
    
    record = MOCK_AADHAAR_REGISTRY[clean_id]
    
    # Verify linking mobile number
    if record["Mobile"] != str(mobile):
        raise AadhaarValidationError("MOBILE_MISMATCH: The provided mobile number does not match the mobile number registered with this Aadhaar.")
        
    return record
