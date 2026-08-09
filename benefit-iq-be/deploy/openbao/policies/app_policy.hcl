# Least-privilege OpenBao Policy for Benefit IQ Backend Application

path "secret/data/benefit-iq-be/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/metadata/benefit-iq-be/*" {
  capabilities = ["read", "list"]
}
