vcl 4.1;

backend github {
    .host = "127.0.0.1";
    .port = "9090";
    .connect_timeout = 5s;
    .first_byte_timeout = 30s;
    .between_bytes_timeout = 10s;
}

sub vcl_recv {
    set req.http.Host = "github.com";

    # Forward all requests to the backend
    if (req.url ~ "^/api/") {
        return (pass);
    }

    if (req.url ~ "\.(tar\.gz|zip|pack|idx)$") {
        return (hash);
    }

    return (pass);
}

sub vcl_backend_response {
    if (bereq.url ~ "\.(tar\.gz|zip|pack|idx)$") {
        set beresp.ttl = 1d;
        set beresp.http.Cache-Control = "public, max-age=86400";
    } else {
        set beresp.ttl = 0s;
        return (pass);
    }
}

sub vcl_deliver {
    unset resp.http.set-cookie;

    # Add cache status header
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}
