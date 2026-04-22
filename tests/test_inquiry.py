def test_home_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Inquiry" in response.data or b"Schedule" in response.data

def test_inquiry_form_post(client):
    data = {
        "name": "Test User",
        "email": "test@example.com",
        "message": "Hello!"
    }
    response = client.post("/inquiry", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Thank you" in response.data