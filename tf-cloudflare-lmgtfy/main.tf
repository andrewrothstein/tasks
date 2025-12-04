# Dummy A record to route traffic through Cloudflare proxy
resource "cloudflare_dns_record" "lmgtfy" {
  zone_id = data.cloudflare_zone.drewfro.id
  name    = "lmgtfy"
  type    = "A"
  content = "192.0.2.1"
  proxied = true
  ttl     = 1
}

resource "cloudflare_ruleset" "lmgtfy_redirect" {
  zone_id = data.cloudflare_zone.drewfro.id
  name    = "lmgtfy redirect"
  kind    = "zone"
  phase   = "http_request_dynamic_redirect"

  rules = [{
    action = "redirect"
    action_parameters = {
      from_value = {
        status_code           = 301
        preserve_query_string = false
        target_url = {
          value = "https://lmgtfy.app"
        }
      }
    }
    expression  = "(http.host eq \"lmgtfy.drewfro.org\")"
    description = "Redirect lmgtfy.drewfro.org to lmgtfy.app"
    enabled     = true
  }]
}
