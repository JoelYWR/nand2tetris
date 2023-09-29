// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
M=M-1
A=M
D=M
A=A-1
D=M-D
M=0
@QAOLTCZW_TRUE
D;JEQ
@QAOLTCZW_END
0;JMP
(QAOLTCZW_TRUE)
@SP
A=M-1
M=-1
(QAOLTCZW_END)
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 16
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
M=M-1
A=M
D=M
A=A-1
D=M-D
M=0
@IPDJQHYY_TRUE
D;JEQ
@IPDJQHYY_END
0;JMP
(IPDJQHYY_TRUE)
@SP
A=M-1
M=-1
(IPDJQHYY_END)
// push constant 16
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
M=M-1
A=M
D=M
A=A-1
D=M-D
M=0
@ECSBLAPR_TRUE
D;JEQ
@ECSBLAPR_END
0;JMP
(ECSBLAPR_TRUE)
@SP
A=M-1
M=-1
(ECSBLAPR_END)
// push constant 892
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
M=M-1
A=M
D=M
A=A-1
D=M-D
M=0
@SWCYRCBL_TRUE
D;JLT
@SWCYRCBL_END
0;JMP
(SWCYRCBL_TRUE)
@SP
A=M-1
M=-1
(SWCYRCBL_END)
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 892
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
M=M-1
A=M
D=M
A=A-1
D=M-D
M=0
@GXZULGVP_TRUE
D;JLT
@GXZULGVP_END
0;JMP
(GXZULGVP_TRUE)
@SP
A=M-1
M=-1
(GXZULGVP_END)
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
M=M-1
A=M
D=M
A=A-1
D=M-D
M=0
@IJLYLAEZ_TRUE
D;JLT
@IJLYLAEZ_END
0;JMP
(IJLYLAEZ_TRUE)
@SP
A=M-1
M=-1
(IJLYLAEZ_END)
// push constant 32767
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
M=M-1
A=M
D=M
A=A-1
D=M-D
M=0
@VSBPQTLW_TRUE
D;JGT
@VSBPQTLW_END
0;JMP
(VSBPQTLW_TRUE)
@SP
A=M-1
M=-1
(VSBPQTLW_END)
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32767
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
M=M-1
A=M
D=M
A=A-1
D=M-D
M=0
@KZXPWACH_TRUE
D;JGT
@KZXPWACH_END
0;JMP
(KZXPWACH_TRUE)
@SP
A=M-1
M=-1
(KZXPWACH_END)
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
M=M-1
A=M
D=M
A=A-1
D=M-D
M=0
@YYYNUVEO_TRUE
D;JGT
@YYYNUVEO_END
0;JMP
(YYYNUVEO_TRUE)
@SP
A=M-1
M=-1
(YYYNUVEO_END)
// push constant 57
@57
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 31
@31
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 53
@53
D=A
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
M=M-1
A=M
D=M
A=A-1
M=D+M
// push constant 112
@112
D=A
@SP
A=M
M=D
@SP
M=M+1
// sub
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
// neg
@SP
A=M-1
M=-M
// and
@SP
M=M-1
A=M
D=M
A=A-1
M=D&M
// push constant 82
@82
D=A
@SP
A=M
M=D
@SP
M=M+1
// or
@SP
M=M-1
A=M
D=M
A=A-1
M=D|M
// not
@SP
A=M-1
M=!M
