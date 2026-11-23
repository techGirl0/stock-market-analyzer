#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"
echo ""

curl -s -X POST http://localhost:8000/api/v1/instruments/AAPL/brief \
  -H "Authorization: Bearer $TOKEN"
