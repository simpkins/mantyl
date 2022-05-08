// Copyright (c) 2022, Adam Simpkins
#include "Layout.h"

namespace ocb {

void KbdV1::qwertyKeymap() {
    using Hid = HidKeyCode;

    auto addMap = [](const PhysicalKey &, Hid) {};

    /*
     * Left half
     */

    // Keys that need to go somewhere:
    // CapsLock
    // Menu

    addMap(L00, Hid::F1);
    addMap(L10, Hid::F2);
    addMap(L20, Hid::F3);
    addMap(L30, Hid::F4);
    addMap(L40, Hid::F5);
    addMap(L50, Hid::F6);

    // addMap(L01, ??); // TODO: ModeChange
    addMap(L11, Hid::N1);
    addMap(L21, Hid::N2);
    addMap(L31, Hid::N3);
    addMap(L41, Hid::N4);
    addMap(L51, Hid::N5);

    addMap(L02, Hid::PageUp); // tbd
    addMap(L12, Hid::Q);
    addMap(L22, Hid::W);
    addMap(L32, Hid::E);
    addMap(L42, Hid::R);
    addMap(L52, Hid::T);
    addMap(L62, Hid::ScrollLock); // tbd

    addMap(L03, Hid::LeftCtrl);
    addMap(L13, Hid::A);
    addMap(L23, Hid::S);
    addMap(L33, Hid::D);
    addMap(L43, Hid::F);
    addMap(L53, Hid::G);
    addMap(L63, Hid::PrintScreen); // tbd

    addMap(L04, Hid::LeftShift);
    addMap(L14, Hid::Z);
    addMap(L24, Hid::X);
    addMap(L34, Hid::C);
    addMap(L44, Hid::V);
    addMap(L54, Hid::B);
    addMap(L64, Hid::NumLock); // tbd

    // addMap(L05, TBD);
    addMap(L15, Hid::Home);
    addMap(L25, Hid::Backslash);
    addMap(L35, Hid::LeftBrace);
    addMap(L45, Hid::Minus);

    /*
     * Left thumb
     */

    addMap(LT00, Hid::Backspace);
    addMap(LT01, Hid::Enter);
    addMap(LT10, Hid::LeftAlt);
    addMap(LT11, Hid::Escape);
    addMap(LT12, Hid::LeftGui);
    // addMap(LT20, TBD);
    addMap(LT21, Hid::Left);
    addMap(LT22, Hid::Up);

    /*
     * Right half
     */
    addMap(R10, Hid::F7);
    addMap(R20, Hid::F8);
    addMap(R30, Hid::F9);
    addMap(R40, Hid::F10);
    addMap(R50, Hid::F11);
    addMap(R60, Hid::F12);

    addMap(R11, Hid::N6);
    addMap(R21, Hid::N7);
    addMap(R31, Hid::N8);
    addMap(R41, Hid::N9);
    addMap(R51, Hid::N0);
    addMap(R61, Hid::Tilde);

    // addMap(R02, TBD); // tbd
    addMap(R12, Hid::Y);
    addMap(R22, Hid::U);
    addMap(R32, Hid::I);
    addMap(R42, Hid::O);
    addMap(R52, Hid::P);
    addMap(R62, Hid::PageDown); // tbd

    // addMap(R03, TBD); // tbd
    addMap(R13, Hid::H);
    addMap(R23, Hid::J);
    addMap(R33, Hid::K);
    addMap(R43, Hid::L);
    addMap(R53, Hid::Semicolon);
    addMap(R63, Hid::RightCtrl);

    // addMap(R04, TBD); // tbd
    addMap(R14, Hid::N);
    addMap(R24, Hid::M);
    addMap(R34, Hid::Comma);
    addMap(R44, Hid::Period);
    addMap(R54, Hid::Quote);
    addMap(R64, Hid::RightShift);

    addMap(R25, Hid::Equal);
    addMap(R35, Hid::RightBrace);
    addMap(R45, Hid::Slash);
    addMap(R55, Hid::End);
    // addMap(R65, TBD); // tbd

    /*
     * Right thumb
     */

    // addMap(RT00, TBD);
    addMap(RT01, Hid::Right);
    addMap(RT02, Hid::Down);
    addMap(RT10, Hid::RightAlt);
    // addMap(RT11, TBD);
    addMap(RT12, Hid::Tab);
    addMap(RT20, Hid::Delete);
    addMap(RT21, Hid::Space);
}

void KbdV1::gamingKeymap() {
    using Hid = HidKeyCode;

    auto addMap = [](const PhysicalKey &, Hid) {};

    /*
     * Left half
     */

    // Keys that need to go somewhere:
    // CapsLock
    // Menu

    addMap(L00, Hid::F1);
    addMap(L10, Hid::F2);
    addMap(L20, Hid::F3);
    addMap(L30, Hid::F4);
    addMap(L40, Hid::F5);
    addMap(L50, Hid::F6);

    // addMap(L01, ??); // TODO: ModeChange
    addMap(L11, Hid::N1);
    addMap(L21, Hid::N2);
    addMap(L31, Hid::N3);
    addMap(L41, Hid::N4);
    addMap(L51, Hid::N5);

    addMap(L02, Hid::ScrollLock);
    addMap(L12, Hid::PageUp);
    addMap(L22, Hid::Q);
    addMap(L32, Hid::W);
    addMap(L42, Hid::E);
    addMap(L52, Hid::R);
    addMap(L62, Hid::T);

    addMap(L03, Hid::Tab);
    addMap(L13, Hid::LeftCtrl);
    addMap(L23, Hid::A);
    addMap(L33, Hid::S);
    addMap(L43, Hid::D);
    addMap(L53, Hid::F);
    addMap(L63, Hid::G);

    addMap(L04, Hid::LeftShift);
    addMap(L14, Hid::LeftShift);
    addMap(L24, Hid::Z);
    addMap(L34, Hid::X);
    addMap(L44, Hid::C);
    addMap(L54, Hid::V);
    addMap(L64, Hid::B);

    addMap(L05, Hid::Tab); // tbd
    addMap(L15, Hid::Home);
    addMap(L25, Hid::Backslash);
    addMap(L35, Hid::LeftBrace);
    addMap(L45, Hid::Minus);

    /*
     * Left thumb
     */

    addMap(LT00, Hid::Backspace);
    addMap(LT01, Hid::Space);
    addMap(LT10, Hid::LeftAlt);
    addMap(LT11, Hid::Escape);
    addMap(LT12, Hid::Enter);
    addMap(LT20, Hid::LeftGui);
    addMap(LT21, Hid::Left);
    addMap(LT22, Hid::Up);

    /*
     * Right half
     */
    addMap(R10, Hid::F7);
    addMap(R20, Hid::F8);
    addMap(R30, Hid::F9);
    addMap(R40, Hid::F10);
    addMap(R50, Hid::F11);
    addMap(R60, Hid::F12);

    addMap(R11, Hid::N6);
    addMap(R21, Hid::N7);
    addMap(R31, Hid::N8);
    addMap(R41, Hid::N9);
    addMap(R51, Hid::N0);
    addMap(R61, Hid::Tilde);

    // addMap(R02, TBD); // tbd
    addMap(R12, Hid::Y);
    addMap(R22, Hid::U);
    addMap(R32, Hid::I);
    addMap(R42, Hid::O);
    addMap(R52, Hid::P);
    addMap(R62, Hid::PageDown); // tbd

    // addMap(R03, TBD); // tbd
    addMap(R13, Hid::H);
    addMap(R23, Hid::J);
    addMap(R33, Hid::K);
    addMap(R43, Hid::L);
    addMap(R53, Hid::Semicolon);
    addMap(R63, Hid::RightCtrl);

    // addMap(R04, TBD); // tbd
    addMap(R14, Hid::N);
    addMap(R24, Hid::M);
    addMap(R34, Hid::Comma);
    addMap(R44, Hid::Period);
    addMap(R54, Hid::Quote);
    addMap(R64, Hid::RightShift);

    addMap(R25, Hid::Equal);
    addMap(R35, Hid::RightBrace);
    addMap(R45, Hid::Slash);
    addMap(R55, Hid::End);
    // addMap(R65, TBD); // tbd

    /*
     * Right thumb
     */

    // addMap(RT00, TBD);
    addMap(RT01, Hid::Right);
    addMap(RT02, Hid::Down);
    addMap(RT10, Hid::RightAlt);
    // addMap(RT11, TBD);
    addMap(RT12, Hid::Tab);
    addMap(RT20, Hid::Delete);
    addMap(RT21, Hid::Space);
}

} // namespace ocb
