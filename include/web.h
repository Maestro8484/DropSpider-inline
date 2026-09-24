// Network side: joins the home network by DHCP (credentials from secrets.ini, or
// a network saved from the page), falls back to its own network DropSpider-setup
// at 192.168.4.1, answers as dropspider.local, serves the web page, and takes
// firmware updates over the network (PlatformIO ota upload, or the page's
// Update card).
#pragma once
#include <Arduino.h>

void webBegin();
void webLoop();
String webWhereAmI();
