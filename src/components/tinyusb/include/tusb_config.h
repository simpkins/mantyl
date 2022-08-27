// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <tusb_option.h>

#define CFG_TUSB_RHPORT0_MODE       OPT_MODE_DEVICE | OPT_MODE_FULL_SPEED
#define CFG_TUSB_OS                 OPT_OS_FREERTOS

#ifndef CFG_TUSB_MEM_SECTION
#define CFG_TUSB_MEM_SECTION
#endif
#ifndef CFG_TUSB_MEM_ALIGN
#define CFG_TUSB_MEM_ALIGN       TU_ATTR_ALIGNED(4)
#endif

#ifndef CFG_TUD_ENDPOINT0_SIZE
#define CFG_TUD_ENDPOINT0_SIZE      64
#endif

#define CFG_TUD_CDC_RX_BUFSIZE      64
#define CFG_TUD_CDC_TX_BUFSIZE      64

// Enabled device class driver
#define CFG_TUD_CDC                 1
#define CFG_TUD_MSC                 0
#define CFG_TUD_HID                 1
#define CFG_TUD_MIDI                0
#define CFG_TUD_CUSTOM_CLASS        0

// MSC is disabled, so this shouldn't matter
#define CFG_TUD_MSC_BUFSIZE         512

// MIDI is disabled, so this shouldn't matter
#define CFG_TUD_MIDI_EP_BUFSIZE     64
#define CFG_TUD_MIDI_EPSIZE         CFG_TUD_MIDI_EP_BUFSIZE
#define CFG_TUD_MIDI_RX_BUFSIZE     64
#define CFG_TUD_MIDI_TX_BUFSIZE     64
