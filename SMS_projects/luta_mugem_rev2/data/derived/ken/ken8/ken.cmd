;-| Super Motions |--------------------------------------------------------

[Command]
name = "combo_xy"
command = ~D,DB,B,x+y

[Command]
name = "combo_xz"
command = ~D,DB,B,x+z

[Command]
name = "combo_yz"
command = ~D,DB,B,y+z

[Command]
name = "sfireball_xy"
command = ~D,DF,F,x+y

[Command]
name = "sfireball_xz"
command = ~D,DF,F,x+z

[Command]
name = "sfireball_yz"
command = ~D,DF,F,y+z

[Command]
name = "shurricane_ab"
command = ~D,DB,B,a+b

[Command]
name = "shurricane_ac"
command = ~D,DB,B,a+c

[Command]
name = "shurricane_bc"
command = ~D,DB,B,b+c

[Command]
name = "reppa_ab"
command = ~D,DF,F,a+b

[Command]
name = "reppa_ac"
command = ~D,DF,F,a+c

[Command]
name = "reppa_bc"
command = ~D,DF,F,b+c

[Command]
name = "sdragon_xy"
command = ~F,D,DF,x+y

[Command]
name = "sdragon_xz"
command = ~F,D,DF,x+z

[Command]
name = "sdragon_yz"
command = ~F,D,DF,y+z

[Command]
name = "ragingd"
command = x,x,F,a,z
time= 30

[Command]
name = "ragingd1"
command = B,F,B,F,s
time= 30

;-| Special Motions |------------------------------------------------------
[Command]
name = "fireball_x"
command = ~D,DF,F,x

[Command]
name = "fireball_y"
command = ~D,DF,F,y

[Command]
name = "fireball_z"
command = ~D,DF,F,z

[Command]
name = "hurricane_a"
command = ~D,DB,B,a

[Command]
name = "hurricane_b"
command = ~D,DB,B,b

[Command]
name = "hurricane_c"
command = ~D,DB,B,c

[Command]
name = "dragonp_x"
command = ~F,D,DF,x

[Command]
name = "dragonp_y"
command = ~F,D,DF,y

[Command]
name = "dragonp_z"
command = ~F,D,DF,z

[Command]
name = "roll_x"
command = ~D,DB,B,x

[Command]
name = "roll_y"
command = ~D,DB,B,y

[Command]
name = "roll_z"
command = ~D,DB,B,z

;-| Dir + Button |---------------------------------------------------------
[Command]
name = "fwd_a"
command = /F,a
time= 1
[Command]
name = "fwd_b"
command = /F,b
time= 1
[Command]
name = "fwd_c"
command = /F,c
time= 1
[Command]
name = "fwd_x"
command = /F,x
time= 1
[Command]
name = "fwd_y"
command = /F,y
time= 1
[Command]
name = "fwd_z"
command = /F,z
time= 1

[Command]
name = "back_a"
command = /B,a
time= 1
[Command]
name = "back_b"
command = /B,b
time= 1
[Command]
name = "back_c"
command = /B,c
time= 1
[Command]
name = "back_x"
command = /B,x
time= 1
[Command]
name = "back_y"
command = /B,y
time= 1
[Command]
name = "back_z"
command = /B,z
time= 1

[Command]
name = "down_a"
command = /D,a
time= 1
[Command]
name = "down_b"
command = /D,b
time= 1
[Command]
name = "down_c"
command = /D,c
time= 1
[Command]
name = "down_x"
command = /D,x
time= 1
[Command]
name = "down_y"
command = /D,y
time= 1
[Command]
name = "down_z"
command = /D,z
time= 1

[Command]
name = "fwd_ab"
command = /F,a+b
time= 1
[Command]
name = "fwd_bc"
command = /F,b+c
time= 1

[Command]
name = "fwd_xy"
command = /F,x+y
time= 1
[Command]
name = "fwd_yz"
command = /F,y+z
time= 1

[Command]
name = "back_xy"
command = /B,x+y
time= 1
[Command]
name = "back_yz"
command = /B,y+z
time= 1

[Command]
name = "back_ab"
command = /B,a+b
time= 1
[Command]
name = "back_bc"
command = /B,b+c
time= 1

;-| Double Tap |-----------------------------------------------------------
[Command]
name = "FF";Required (do not remove)
command = F,F
time= 10

[Command]
name = "BB";Required (do not remove)
command = B,B
time= 10

;-| 2/3 Button Combination |-----------------------------------------------
[Command]
name = "recovery";Required (do not remove)
command = a+b
time= 1

[Command]
name = "ab"
command = a+b
time= 1

;-| Single Button |---------------------------------------------------------
[Command]
name = "a"
command = a
time= 1

[Command]
name = "b"
command = b
time= 1

[Command]
name = "c"
command = c
time= 1

[Command]
name = "x"
command = x
time= 1

[Command]
name = "y"
command = y
time= 1

[Command]
name = "z"
command = z
time= 1

[Command]
name = "s"
command = s
time= 1

;-| Hold Button |-----------------------------------------------------------
[Command]
name = "hold_x"
command = /x
time= 1

[Command]
name = "hold_y"
command = /y
time= 1

[Command]
name = "hold_z"
command = /z
time= 1

[Command]
name = "hold_a"
command = /a
time= 1

[Command]
name = "hold_b"
command = /b
time= 1

[Command]
name = "hold_c"
command = /c
time= 1

;-| Hold Dir |--------------------------------------------------------------
[Command]
name = "holdfwd";Required (do not remove)
command = /$F
time= 1

[Command]
name = "holdback";Required (do not remove)
command = /$B
time= 1

[Command]
name = "holdup";Required (do not remove)
command = /$U
time= 1

[Command]
name = "holddown";Required (do not remove)
command = /$D
time= 1

;---------------------------------------------------------------------------
; Commands
[Statedef -1]

;===========================================================================

;---------------------------------------------------------------------------
;RunFwd
[State -1]
type = ChangeState
value = 100
trigger1 = command = "FF"
trigger1 = statetype = S
trigger1 = ctrl = 1

;---------------------------------------------------------------------------
;RunBack
[State -1]
type = ChangeState
value = 105
trigger1 = command = "BB"
trigger1 = statetype = S
trigger1 = ctrl = 1

;=========================================================================
;Reppa
[State -1]
type = ChangeState
value = 2100
triggerall = power >= 1000
triggerall = command = "sfireball_xy"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;=========================================================================
;Reppa
[State -1]
type = ChangeState
value = 2100
triggerall = power >= 1000
triggerall = command = "sfireball_yz"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;=========================================================================
;Reppa
[State -1]
type = ChangeState
value = 2100
triggerall = power >= 1000
triggerall = command = "sfireball_xz"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;=========================================================================
;Reppa
[State -1]
type = ChangeState
value = 2200
triggerall = power >= 1000
triggerall = command = "reppa_ab"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;=========================================================================
;Reppa
[State -1]
type = ChangeState
value = 2200
triggerall = power >= 1000
triggerall = command = "reppa_ac"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;=========================================================================
;Reppa
[State -1]
type = ChangeState
value = 2200
triggerall = power >= 1000
triggerall = command = "reppa_bc"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;---------------------------------------------------------------------------
;Counter Dragon Punch
[State -1]
type = ChangeState
value = 1203
triggerall = command = "sfireball_xy"
triggerall = power >= 500
trigger1 = stateno = 150
trigger2 = stateno = 151
trigger3 = stateno = 152
trigger4 = stateno = 153

;---------------------------------------------------------------------------
;Counter Dragon Punch
[State -1]
type = ChangeState
value = 1203
triggerall = command = "sfireball_xz"
triggerall = power >= 500
trigger1 = stateno = 150
trigger2 = stateno = 151
trigger3 = stateno = 152
trigger4 = stateno = 153

;---------------------------------------------------------------------------
;Counter Dragon Punch
[State -1]
type = ChangeState
value = 1203
triggerall = command = "sfireball_yz"
triggerall = power >= 500
trigger1 = stateno = 150
trigger2 = stateno = 151
trigger3 = stateno = 152
trigger4 = stateno = 153

;---------------------------------------------------------------------------
;Counter Dragon Punch
[State -1]
type = ChangeState
value = 1203
triggerall = command = "reppa_ab"
triggerall = power >= 500
trigger1 = stateno = 150
trigger2 = stateno = 151
trigger3 = stateno = 152
trigger4 = stateno = 153

;---------------------------------------------------------------------------
;Counter Dragon Punch
[State -1]
type = ChangeState
value = 1203
triggerall = command = "reppa_ac"
triggerall = power >= 500
trigger1 = stateno = 150
trigger2 = stateno = 151
trigger3 = stateno = 152
trigger4 = stateno = 153

;---------------------------------------------------------------------------
;Counter Dragon Punch
[State -1]
type = ChangeState
value = 1203
triggerall = command = "reppa_bc"
triggerall = power >= 500
trigger1 = stateno = 150
trigger2 = stateno = 151
trigger3 = stateno = 152
trigger4 = stateno = 153

;=========================================================================
;Shippu
[State -1]
type = ChangeState
value = 2000
triggerall = power >= 1000
triggerall = command = "shurricane_ab"
trigger1 = statetype != A
trigger1 = ctrl = 1

;=========================================================================
;Shippu
[State -1]
type = ChangeState
value = 2000
triggerall = power >= 1000
triggerall = command = "shurricane_bc"
trigger1 = statetype != A
trigger1 = ctrl = 1

;=========================================================================
;Shippu
[State -1]
type = ChangeState
value = 2000
triggerall = power >= 1000
triggerall = command = "shurricane_ac"
trigger1 = statetype != A
trigger1 = ctrl = 1

;---------------------------------------------------------------------------
;Dragon Punch_X
[State -1]
type = ChangeState
value = 1200
triggerall = command = "dragonp_x"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;---------------------------------------------------------------------------
;Dragon Punch_Y
[State -1]
type = ChangeState
value = 1201
triggerall = command = "dragonp_y"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;---------------------------------------------------------------------------
;Dragon Punch_Z
[State -1]
type = ChangeState
value = 1202
triggerall = command = "dragonp_z"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;Roll_x
[State -1]
type = ChangeState
value = 1300
trigger1 = command = "roll_x"
trigger1 = ctrl = 1
trigger1 = statetype != A

;Roll_y
[State -1]
type = ChangeState
value = 1301
trigger1 = command = "roll_y"
trigger1 = ctrl = 1
trigger1 = statetype != A

;Roll_z
[State -1]
type = ChangeState
value = 1302
trigger1 = command = "roll_z"
trigger1 = ctrl = 1
trigger1 = statetype != A

;---------------------------------------------------------------------------
;Hurricane_a
[State -1]
type = ChangeState
value = 1100
triggerall = command = "hurricane_a"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;Hurricane_b
[State -1]
type = ChangeState
value = 1101
triggerall = command = "hurricane_b"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;Hurricane_c
[State -1]
type = ChangeState
value = 1102
triggerall = command = "hurricane_c"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact
trigger11 = stateno = 240
trigger11 = MoveContact

;---------------------------------------------------------------------------
;Air Hurricane_a
[State -1]
type = ChangeState
value = 1103
triggerall = command = "hurricane_a"
trigger1 = statetype = A
trigger1 = ctrl = 1

;Air Hurricane_b
[State -1]
type = ChangeState
value = 1104
triggerall = command = "hurricane_b"
trigger1 = statetype = A
trigger1 = ctrl = 1

;Air Hurricane_c
[State -1]
type = ChangeState
value = 1105
triggerall = command = "hurricane_c"
trigger1 = statetype = A
trigger1 = ctrl = 1

;Fireball_x
[State -1]
type = ChangeState
value = 1000
triggerall = command = "fireball_x"
triggerall = numproj = 0
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact

;Fireball_y
[State -1]
type = ChangeState
value = 1010
triggerall = command = "fireball_y"
triggerall = numproj = 0
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact

;Fireball_z
[State -1]
type = ChangeState
value = 1020
triggerall = command = "fireball_z"
triggerall = numproj = 0
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = MoveContact
trigger3 = stateno = 210
trigger3 = MoveContact
trigger4 = stateno = 220
trigger4 = MoveContact
trigger5 = stateno = 230
trigger5 = MoveContact
trigger6 = stateno = 400
trigger6 = MoveContact
trigger7 = stateno = 410
trigger7 = MoveContact
trigger8 = stateno = 420
trigger8 = MoveContact
trigger9 = stateno = 430
trigger9 = MoveContact
trigger10 = stateno = 440
trigger10 = MoveContact

;Axe kick
[State -1]
type = ChangeState
value = 280
triggerall = command = "fwd_b"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger2 = stateno = 100

;Stand_X
[State -1]
type = ChangeState
value = 200
triggerall = command = "x"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = time> 5

;Stand_Y
[State -1]
type = ChangeState
value = 210
triggerall = command = "y"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1

;Stand_Z
[State -1]
type = ChangeState
value = 220
triggerall = command = "z"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1

;Stand_A
[State -1]
type = ChangeState
value = 250
triggerall = command = "a"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1

;Stand_B
[State -1]
type = ChangeState
value = 260
triggerall = command = "b"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1

;Stand_C
[State -1]
type = ChangeState
value = 270
triggerall = command = "c"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1

;Crouch_X
[State -1]
type = ChangeState
value = 400
triggerall = command = "x"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl = 1

;Crouch_Y
[State -1]
type = ChangeState
value = 410
triggerall = command = "y"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl = 1

;Crouch_Z
[State -1]
type = ChangeState
value = 420
triggerall = command = "z"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl = 1

;Crouch_A
[State -1]
type = ChangeState
value = 430
triggerall = command = "a"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl = 1

;Crouch_B
[State -1]
type = ChangeState
value = 440
triggerall = command = "b"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl = 1

;Crouch_C
[State -1]
type = ChangeState
value = 450
triggerall = command = "c"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl = 1

;Aerial Rave Jump
[State -1]
type = ChangeState
value = 40
triggerall = command = "holdup"
trigger1 = MoveHit
trigger1 = stateno = 420

;---------------------------------------------------------------------------
;Jump_X
[State -1]
type = ChangeState
value = 600
triggerall = command = "x"
trigger1 = statetype = A
trigger1 = ctrl = 1
;trigger2 = command = a   ;-------
;trigger2 = stateno = 600 ;jump_a
;trigger2 = statetime >= 6
;trigger2 = p2statetype = A

;---------------------------------------------------------------------------
;Jump_Y
[State -1]
type = ChangeState
value = 610
triggerall = command = "y"
trigger1 = statetype = A
trigger1 = ctrl = 1
trigger2 = stateno = 630
trigger2 = MoveContact
trigger2 = p2statetype = A
trigger3 = stateno = 660
trigger3 = MoveContact
trigger3 = p2statetype = A
;---------------------------------------------------------------------------
;Jump_Z
[State -1]
type = ChangeState
value = 620
triggerall = command = "z"
trigger1 = statetype = A
trigger1 = ctrl = 1
trigger2 = stateno = 640
trigger2 = MoveContact
trigger2 = p2statetype = A
trigger3 = stateno = 670
trigger3 = MoveContact
trigger3 = p2statetype = A

;---------------------------------------------------------------------------
;Jump_A
[State -1]
type = ChangeState
value = 630
triggerall = Vel X = 0
triggerall = command = "a"
trigger1 = statetype = A
trigger1 = ctrl = 1
trigger2 = stateno = 600
trigger2 = MoveContact
trigger2 = p2statetype = A

;---------------------------------------------------------------------------
;Jump_B
[State -1]
type = ChangeState
value = 640
triggerall = Vel X = 0
triggerall = command = "b"
trigger1 = statetype = A
trigger1 = ctrl = 1
trigger2 = stateno = 610
trigger2 = MoveContact
trigger2 = p2statetype = A

;---------------------------------------------------------------------------
;Jump_C
[State -1]
type = ChangeState
value = 650
triggerall = Vel X = 0
triggerall = command = "c"
trigger1 = statetype = A
trigger1 = ctrl = 1
trigger2 = stateno = 640
trigger2 = MoveContact
trigger2 = p2statetype = A
trigger3 = stateno = 670
trigger3 = p2statetype = A
trigger3 = MoveContact
;---------------------------------------------------------------------------
;Jump_A
[State -1]
type = ChangeState
value = 660
triggerall = Vel X != 0
triggerall = command = "a"
trigger1 = statetype = A
trigger1 = ctrl = 1
trigger2 = stateno = 600
trigger2 = MoveContact
trigger2 = p2statetype = A
;---------------------------------------------------------------------------
;Jump_B
[State -1]
type = ChangeState
value = 670
triggerall = Vel X != 0
triggerall = command = "b"
trigger1 = statetype = A
trigger1 = ctrl = 1
trigger2 = stateno = 610
trigger2 = MoveContact
trigger2 = p2statetype = A

;---------------------------------------------------------------------------
;Jump_C
[State -1]
type = ChangeState
value = 680
triggerall = Vel X != 0
triggerall = command = "c"
trigger1 = statetype = A
trigger1 = ctrl = 1
trigger2 = stateno = 640
trigger2 = MoveContact
trigger2 = p2statetype = A
trigger3 = stateno = 670
trigger3 = MoveContact
trigger3 = p2statetype = A

;---------------------------------------------------------------------------
;Taunt
[State -1]
type = ChangeState
value = 195
triggerall = command = "s"
trigger1 = statetype = S
trigger1 = ctrl = 1
