# Security Policy

## Supported Versions

Currently maintained versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Features

### Implemented Security Controls

✅ **Credential Encryption**
- All API keys and private keys encrypted at rest using Fernet (AES-256)
- PBKDF2 key derivation with 480,000 iterations (OWASP recommended)
- Master password required for decryption

✅ **Input Validation**
- All user inputs sanitized and validated
- Type checking on API parameters
- Range validation on prices and quantities
- Protection against injection attacks

✅ **Circuit Breaker**
- Automatic trading halt on excessive losses
- Daily loss limit (default: 5%)
- Drawdown protection (default: 15%)
- Prevents runaway financial losses

✅ **Partial Fill Protection**
- Automatic position unwinding on failed arbitrage legs
- Prevents naked directional exposure
- Immediate risk mitigation

✅ **Error Handling**
- Comprehensive exception handling
- Secure error messages (no sensitive data exposure)
- Detailed logging for debugging

✅ **Dependency Management**
- Regular security audits
- No known vulnerable dependencies
- Automated updates via dependabot (recommended)

---

## Known Security Considerations

### ⚠️  High Priority

1. **Private Key Storage**
   - Private keys are encrypted but still stored locally
   - **Mitigation**: Use hardware wallet integration (future enhancement)
   - **Current**: Ensure filesystem encryption and secure backups

2. **Master Password**
   - Single point of failure
   - **Mitigation**: Use strong, unique password stored in password manager
   - **Recommendation**: 20+ characters, mix of types

3. **API Response Verification**
   - HMAC signature verification for Kalshi responses not fully implemented
   - **Mitigation**: Validate critical data from multiple sources
   - **Status**: Planned for v1.1

### ⚠️  Medium Priority

4. **Rate Limiting**
   - Rate limiting configured but not enforced in all edge cases
   - **Mitigation**: Monitor API usage, implement backoff

5. **Session Management**
   - HTTP sessions reused without regular rotation
   - **Mitigation**: Restart bot daily
   - **Planned**: Automatic session rotation (v1.1)

6. **Dashboard Authentication**
   - Streamlit dashboard has no built-in authentication
   - **Mitigation**: Only run locally or behind VPN
   - **Recommendation**: Use reverse proxy with basic auth

---

## Reporting a Vulnerability

### What to Report

Please report:
- Authentication bypass
- Credential exposure
- Code injection vulnerabilities
- Financial loss mechanisms
- Denial of service attacks
- Any security-related bug

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

**Instead:**
1. Email: [Your contact email - REPLACE THIS]
2. Subject: "SECURITY: Orion Arbitrage - [Brief Description]"
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **24 hours**: Initial acknowledgment
- **72 hours**: Initial assessment and severity rating
- **7 days**: Fix or mitigation plan
- **30 days**: Patch released (for critical issues)

### Disclosure Policy

- We practice **coordinated disclosure**
- Security researchers will be credited (if desired)
- Public disclosure after fix is available
- CVE assigned for significant vulnerabilities

---

## Security Best Practices for Users

### Essential Security Measures

1. **Credential Management**
   ```bash
   # Always use encrypted credentials
   python -m src.utils.secrets_manager

   # Never commit .env files
   git update-index --assume-unchanged .env
   ```

2. **Master Password**
   - Minimum 20 characters
   - Use password manager (1Password, Bitwarden, etc.)
   - Never store in code or logs
   - Rotate monthly

3. **API Key Permissions**
   - Kalshi: Trading only (no withdrawals if possible)
   - Polymarket: Separate wallet for trading
   - Review permissions monthly

4. **Network Security**
   - Run on secure network
   - Use VPN if on public WiFi
   - Consider running in isolated VM

5. **Monitoring**
   ```bash
   # Check for unauthorized access
   tail -f logs/arbitrage.log | grep ERROR

   # Monitor exchange balances
   # Review database for unexpected trades
   sqlite3 data/arbitrage.db "SELECT * FROM trades WHERE success=0;"
   ```

6. **Regular Updates**
   ```bash
   # Update dependencies weekly
   pip install --upgrade -r requirements.txt

   # Check for security advisories
   pip audit  # or: safety check
   ```

### Advanced Security

7. **Filesystem Encryption**
   - Linux: LUKS, eCryptfs
   - macOS: FileVault
   - Windows: BitLocker

8. **Process Isolation**
   ```bash
   # Run in Docker container
   docker-compose up -d

   # Or use systemd hardening
   # See PRODUCTION_SETUP.md
   ```

9. **Backup Encryption**
   ```bash
   # Encrypt database backups
   gpg --symmetric data/arbitrage.db

   # Store offsite
   ```

10. **Audit Logging**
    - Enable detailed logging
    - Review logs daily
    - Archive logs securely

---

## Security Audit Checklist

Before production deployment:

### Credentials
- [ ] All API keys encrypted
- [ ] Master password in password manager
- [ ] `.env` file excluded from git
- [ ] API keys have minimum required permissions
- [ ] Separate dev/prod credentials

### Configuration
- [ ] Circuit breaker enabled
- [ ] Conservative position limits
- [ ] Auto-execute disabled initially
- [ ] Risk parameters validated

### Infrastructure
- [ ] Secure network connection
- [ ] Filesystem encryption enabled
- [ ] Regular backups configured
- [ ] Monitoring and alerts configured

### Code
- [ ] Latest dependencies installed
- [ ] No hardcoded secrets
- [ ] Input validation enabled
- [ ] Error handling comprehensive

### Operational
- [ ] Dry-run tested 24+ hours
- [ ] Emergency stop procedure documented
- [ ] Incident response plan ready
- [ ] Regular security reviews scheduled

---

## Compliance & Legal

### Regulatory Considerations

⚠️  **User Responsibility**

You are responsible for ensuring compliance with:

- Local gambling/trading regulations
- Tax reporting requirements
- KYC/AML compliance
- Securities laws (if applicable)
- Data protection laws (GDPR, etc.)

**Polymarket**:
- Geographic restrictions (US users restricted)
- Ensure you're in a permitted jurisdiction

**Kalshi**:
- CFTC-regulated (US)
- Requires US residency and identity verification

### Data Handling

**Personal Data Collected**:
- None directly by the bot
- Exchange APIs may log IP addresses
- Telegram alerts contain trading data

**Data Storage**:
- Local SQLite database (encrypted filesystem recommended)
- No cloud storage by default
- User responsible for data security

**Data Retention**:
- Trade logs retained indefinitely (configurable)
- Recommendation: 7 years for tax purposes
- User can delete anytime

---

## Incident Response

### If Credentials Are Compromised

1. **Immediately**:
   ```bash
   # Stop the bot
   pkill -f "python main.py"
   ```

2. **Revoke Access**:
   - Deactivate API keys on exchanges
   - Transfer funds to new wallet (Polymarket)
   - Generate new API credentials

3. **Assess Damage**:
   ```bash
   # Check recent trades
   sqlite3 data/arbitrage.db "SELECT * FROM trades ORDER BY created_at DESC LIMIT 20;"

   # Review logs
   grep ERROR logs/arbitrage.log
   ```

4. **Secure System**:
   - Change master password
   - Re-encrypt all credentials
   - Scan system for malware
   - Review access logs

5. **Re-deploy**:
   - Fresh .env file
   - New encrypted credentials
   - Verify no unauthorized access

### If Unauthorized Trades Detected

1. **Stop Trading**:
   ```bash
   # Halt immediately
   pkill -f "python main.py"
   ```

2. **Cancel Open Orders**:
   - Manually cancel on exchanges
   - Verify no pending orders

3. **Close Positions**:
   - Review open positions
   - Close manually if needed
   - Document all actions

4. **Investigate**:
   - Review logs for anomalies
   - Check code for bugs
   - Verify API credentials secure

5. **Report** (if needed):
   - Contact exchange support
   - Report to security team
   - File police report (if fraud)

---

## Security Roadmap

### Planned Enhancements (v1.1)

- [ ] HMAC response verification for all API calls
- [ ] Hardware wallet integration (Ledger/Trezor)
- [ ] Multi-signature wallet support
- [ ] Automatic session rotation
- [ ] Two-factor authentication for bot commands
- [ ] Encrypted database storage
- [ ] Audit log immutability (blockchain)
- [ ] Rate limiting enforcement
- [ ] Automated penetration testing
- [ ] SOC 2 compliance (future)

### Future Considerations (v2.0+)

- [ ] Zero-knowledge proofs for privacy
- [ ] Secure enclave execution
- [ ] Distributed key management
- [ ] MFA for critical operations
- [ ] Anomaly detection AI
- [ ] Bug bounty program

---

## Security Contact

**For security issues ONLY:**
- Email: [REPLACE with your email]
- PGP Key: [REPLACE with your PGP fingerprint]
- Response Time: 24 hours

**For general issues:**
- GitHub Issues: https://github.com/[your-repo]/issues
- Documentation: See PRODUCTION_SETUP.md

---

## Acknowledgments

We thank security researchers who responsibly disclose vulnerabilities:

- [Your name here - for initial security audit]
- [Future contributors]

---

**Last Updated**: October 22, 2025
**Next Review**: November 22, 2025

**Remember**: Security is a continuous process, not a one-time checklist. Stay vigilant! 🔒
