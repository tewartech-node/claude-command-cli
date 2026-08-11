package metrics

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// Handler returns the HTTP handler for Prometheus metrics
func Handler() http.Handler {
	return promhttp.Handler()
}

// StartMetricsServer starts a metrics server on the given address
func StartMetricsServer(addr string) error {
	http.Handle("/metrics", Handler())
	go http.ListenAndServe(addr, nil)
	return nil
}
