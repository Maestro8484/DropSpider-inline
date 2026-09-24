// The console: one set of text commands, reachable from the USB serial port and
// from the Console card on the web page. Every reply and every machine message
// goes to both, so either one shows the whole story.
#pragma once
#include <Arduino.h>

// Print a line to the serial port and to the web page's log.
void logf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));

// Run one command line. Replies go through logf. If capture is given, the reply
// lines are also appended to it (the web page uses this for its instant answer).
void consoleRun(const String &line, String *capture = nullptr);

// Read any typed characters from the USB serial port and run complete lines.
void consolePollSerial();

// Log lines numbered from 1. Returns lines with number > since as a JSON array
// body, and sets next to the number to ask from next time.
String logJsonSince(uint32_t since, uint32_t &next);
