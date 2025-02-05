vcl 4.1;

# Health check backend
backend default {
    .host = "github.com";
    .port = "443";
}

# Main Git backend
backend git_backend {
    .host = "${GIT_BACKEND_HOST}";
    .port = "${GIT_BACKEND_PORT}";
    .probe = {
        .url = "/";
        .timeout = 2s;
        .interval = 5s;
        .window = 5;
        .threshold = 3;
    }
}

sub vcl_recv {
    # Only cache GET and HEAD requests
    if (req.method != "GET" && req.method != "HEAD") {
        return (pass);
    }

    # Skip cache for authenticated requests
    if (req.http.Authorization) {
        return (pass);
    }

    # Cache git objects and pack files
    if (req.url ~ "^/.*?/(?:info/refs|git-upload-pack|objects/[0-9a-f]{2}/[0-9a-f]{38}|objects/pack/pack-[0-9a-f]{40}.pack)") {
        unset req.http.Cookie;
        return (hash);
    }

    # Don't cache everything else
    return (pass);
}

sub vcl_backend_response {
    # Set cache time for different Git objects
    if (bereq.url ~ "^/.*?/objects/[0-9a-f]{2}/[0-9a-f]{38}$") {
        # Loose objects - cache for 24h
        set beresp.ttl = 24h;
        set beresp.grace = 1h;
    } elsif (bereq.url ~ "^/.*?/objects/pack/pack-[0-9a-f]{40}.pack$") {
        # Pack files - cache for 24h
        set beresp.ttl = 24h;
        set beresp.grace = 1h;
    } elsif (bereq.url ~ "^/.*?/info/refs") {
        # Refs - cache for 1m
        set beresp.ttl = 1m;
        set beresp.grace = 10s;
    }

    # Enable streaming for large files
    if (beresp.http.content-length ~ "[0-9]{7,}") {
        set beresp.do_stream = true;
    }

    # Remove cookies from cached responses
    unset beresp.http.set-cookie;
    return (deliver);
}

sub vcl_deliver {
    # Add cache status header
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}
