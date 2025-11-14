# Add User Authentication

Implement basic email/password authentication:
- User registration endpoint (POST /api/register)
- Login endpoint (POST /api/login)
- JWT token generation (60-minute expiry)
- Password hashing with bcrypt (salt rounds: 10)
- Basic input validation

## Technical Details
- Backend: Express.js REST API
- Database: PostgreSQL (users table)
- Authentication: JWT with refresh tokens
- Security: HTTPS only, rate limiting

## Acceptance Criteria
- [ ] Users can register with email/password
- [ ] Users can login and receive JWT
- [ ] Passwords are never stored in plaintext
- [ ] Invalid credentials return 401 Unauthorized
- [ ] Rate limiting prevents brute force attacks

Estimated: 2-3 days
Complexity: Simple to Moderate
