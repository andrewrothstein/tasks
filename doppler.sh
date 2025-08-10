doppler_create_k8s_secret() {
    local name=$1
    kubectl create secret generic \
            $name \
            --from-env-file <(doppler secrets download --no-file --format docker)
}

doppler_template() {
    envsubst <<EOF
rootToken: $VAULT_ROOT_TOKEN
EOF
}
