package log

import (
	"fmt"
	"os"
	"sync/atomic"
	"time"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

var (
	globalLogger *zap.Logger
	globalSugared *zap.SugaredLogger
	requestID atomic.Uint64
)

// Level represents log level
type Level string

const (
	LevelDebug Level = "DEBUG"
	LevelInfo  Level = "INFO"
	LevelWarn  Level = "WARN"
	LevelError Level = "ERROR"
	LevelFatal Level = "FATAL"
)

// Init initializes the global logger
func Init(level string) error {
	// Configure zap
	config := zap.NewProductionConfig()

	// Parse log level
	switch level {
	case "debug":
		config.Level = zap.NewAtomicLevelAt(zapcore.DebugLevel)
	case "info":
		config.Level = zap.NewAtomicLevelAt(zapcore.InfoLevel)
	case "warn":
		config.Level = zap.NewAtomicLevelAt(zapcore.WarnLevel)
	case "error":
		config.Level = zap.NewAtomicLevelAt(zapcore.ErrorLevel)
	default:
		config.Level = zap.NewAtomicLevelAt(zapcore.InfoLevel)
	}

	// JSON output for structured logging
	config.Encoding = "json"
	config.EncoderConfig.TimeKey = "timestamp"
	config.EncoderConfig.LevelKey = "level"
	config.EncoderConfig.NameKey = "logger"
	config.EncoderConfig.CallerKey = "caller"
	config.EncoderConfig.FunctionKey = "function"
	config.EncoderConfig.MessageKey = "message"
	config.EncoderConfig.StacktraceKey = "stacktrace"
	config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

	logger, err := config.Build()
	if err != nil {
		return fmt.Errorf("failed to initialize logger: %w", err)
	}

	globalLogger = logger
	globalSugared = logger.Sugar()

	return nil
}

// GetRequestID generates a unique request ID
func GetRequestID() string {
	id := requestID.Add(1)
	return fmt.Sprintf("%d-%d", time.Now().Unix(), id)
}

// Infof logs an info message with request context
func Infof(requestID, format string, args ...interface{}) {
	globalSugared.Infow(fmt.Sprintf(format, args...),
		"request_id", requestID,
	)
}

// Warnf logs a warning message
func Warnf(requestID, format string, args ...interface{}) {
	globalSugared.Warnw(fmt.Sprintf(format, args...),
		"request_id", requestID,
	)
}

// Errorf logs an error message with context
func Errorf(requestID, format string, args ...interface{}) {
	globalSugared.Errorw(fmt.Sprintf(format, args...),
		"request_id", requestID,
	)
}

// ErrorContext logs an error with structured fields
func ErrorContext(requestID string, message string, fields map[string]interface{}) {
	fields["request_id"] = requestID
	f := make([]interface{}, 0, len(fields)*2)
	for k, v := range fields {
		f = append(f, k, v)
	}
	globalSugared.Errorw(message, f...)
}

// InfoContext logs info with structured fields
func InfoContext(requestID string, message string, fields map[string]interface{}) {
	fields["request_id"] = requestID
	f := make([]interface{}, 0, len(fields)*2)
	for k, v := range fields {
		f = append(f, k, v)
	}
	globalSugared.Infow(message, f...)
}

// CommandStarted logs the start of a command
func CommandStarted(requestID, command string, args map[string]interface{}) {
	args["request_id"] = requestID
	args["event"] = "command_started"
	args["timestamp"] = time.Now()
	f := make([]interface{}, 0, len(args)*2)
	for k, v := range args {
		f = append(f, k, v)
	}
	globalSugared.Infow(command, f...)
}

// CommandCompleted logs successful command completion
func CommandCompleted(requestID, command string, durationMs int64) {
	globalSugared.Infow("command_completed",
		"request_id", requestID,
		"command", command,
		"duration_ms", durationMs,
		"status", "success",
	)
}

// CommandFailed logs command failure
func CommandFailed(requestID, command string, durationMs int64, err error) {
	globalSugared.Errorw("command_failed",
		"request_id", requestID,
		"command", command,
		"duration_ms", durationMs,
		"error", err.Error(),
		"status", "error",
	)
}

// EncryptionStarted logs encryption operation
func EncryptionStarted(requestID string, dataSize int) {
	globalSugared.Debugw("encryption_started",
		"request_id", requestID,
		"data_size_bytes", dataSize,
	)
}

// EncryptionCompleted logs successful encryption
func EncryptionCompleted(requestID string, durationMs int64) {
	globalSugared.Debugw("encryption_completed",
		"request_id", requestID,
		"duration_ms", durationMs,
	)
}

// EncryptionFailed logs encryption failure
func EncryptionFailed(requestID string, err error) {
	globalSugared.Errorw("encryption_failed",
		"request_id", requestID,
		"error", err.Error(),
		"alert", true,  // Trigger alert
	)
}

// NetworkRequest logs outbound network request
func NetworkRequest(requestID, method, url string) {
	globalSugared.Debugw("network_request_start",
		"request_id", requestID,
		"method", method,
		"url", url,
	)
}

// NetworkResponse logs network response
func NetworkResponse(requestID string, statusCode int, durationMs int64) {
	globalSugared.Debugw("network_request_complete",
		"request_id", requestID,
		"status_code", statusCode,
		"duration_ms", durationMs,
	)
}

// NetworkError logs network failure
func NetworkError(requestID string, err error, retryCount int) {
	globalSugared.Warnw("network_error",
		"request_id", requestID,
		"error", err.Error(),
		"retry_count", retryCount,
	)
}

// Sync flushes pending logs
func Sync() error {
	if globalLogger != nil {
		return globalLogger.Sync()
	}
	return nil
}

// Fatal logs a fatal error and exits
func Fatal(requestID, message string, err error) {
	globalSugared.Errorw(message,
		"request_id", requestID,
		"error", err.Error(),
		"level", "FATAL",
	)
	globalLogger.Sync()
	os.Exit(1)
}
