# OpenBao Production Configuration (HCL Format)
# Hardened for Production deployment with Raft Storage and TLS encryption.

ui = true
disable_mlock = false

storage "raft" {
  path    = "/bao/data"
  node_id = "node1"
}

listener "tcp" {
  address         = "0.0.0.0:8200"
  tls_cert_file   = "/bao/tls/bao.crt"
  tls_key_file    = "/bao/tls/bao.key"
  tls_min_version = "tls12"
}

api_addr     = "https://127.0.0.1:8200"
cluster_addr = "https://127.0.0.1:8201"
