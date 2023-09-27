resource "smallstep_authority" "basic" {
  type              = "devops"
  active_revocation = false
  admin_emails      = ["andrew.rothstein@gmail.com"]
  name              = "nj"
  subdomain         = "ca.drewfus"
}

output "bootstrap_basic" {
  value = "step ca bootstrap --ca-url https://${smallstep_authority.basic.domain} --fingerprint ${smallstep_authority.basic.fingerprint} --context basic"
}
