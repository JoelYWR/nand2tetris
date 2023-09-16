// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

    @pxl
    M=0

    @8191
    D=A

    @screenmapsize
    M=D

(LOOP)
    @KBD
    D=M

    @TURN_SCREEN_BLACK
    D;JGT

    @TURN_SCREEN_WHITE
    D;JEQ

    @LOOP
    0;JMP

(TURN_SCREEN_BLACK)
    @pxl
    D=M

    @LOOP
    D+1;JEQ

    @i
    M=0

    @UPDATE_SCREEN
    0;JMP

(TURN_SCREEN_WHITE)
    @pxl
    D=M

    @LOOP
    D;JEQ

    @i
    M=0

    @UPDATE_SCREEN
    0;JMP

(UPDATE_SCREEN)
    @i
    D=M

    @screenmapsize
    D=D-M

    @QUIT_UPDATE_SCREEN
    D;JGT

    @i
    D=M

    @SCREEN
    A=A+D
    M=!M

    @i
    M=M+1

    @UPDATE_SCREEN
    0;JMP

(QUIT_UPDATE_SCREEN)
    @SCREEN
    D=M

    @pxl
    M=D

    @LOOP
    0;JMP
