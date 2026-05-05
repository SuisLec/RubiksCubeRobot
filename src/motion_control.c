/******************************************************************************
 * @file    motion_control.c
 * @brief   步进电机加减速曲线 & 运动控制 (HSI 8MHz + CPU延时版本)
 *
 * 动作编码:
 *   L_C:0  R_C:5   (Close/闭合手爪)
 *   L_O:1  R_O:6   (Open/张开手爪)
 *   L_1:2  R_1:7   (正转90度)
 *   L_2:3  R_2:8   (转180度, 智能方向选择以避免缠管)
 *   L_3:4  R_3:9   (逆转90度)
 *
 * 气管缠绕约束: 每臂同向累计不超过 ±3 (即270°)
 *   超过时自动张开手爪反向收管, 再继续执行动作
 ******************************************************************************/
#include "motion_control.h"
#include "delay.h"
#include "step_motor.h"
#include "cylinder.h"
#include "robot.h"

const int MotorSub = 3200;  /* 16细分: 3200脉冲/圈 */

/* ========= 加减速曲线参数 (delay值单位: ×5us) ========= */

/* 空转90度 */
static int KZ90Ac[] = {
78,60,51,45,40,37,34,32,31,29,28,27,26,25,24,23,23,22,21,21,20,20,19,
19,19,18,18,18,17,17,17,17,16,16,16,16,15,15,15,15,15,14,14,14,14,14,14,14,
13,13,13,13,13,13,13,13,12,12,12,12,12,12,12,12,12,12,11,11,11,11,11,11,11,
11,11,11,11,11,11,11,11,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,
9,9,9,9,9,9,9,9,9,9,9
};

/* 空转180度 */
static int KZ180Ac[] = {
56,53,51,49,47,46,44,43,42,41,40,39,38,37,
36,36,35,34,34,33,33,32,32,31,31,30,30,29,29,29,28,28,28,27,27,27,26,26,26,
26,25,25,25,25,24,24,24,24,24,23,23,23,23,23,22,22,22,22,22,22,21,21,21,21,
21,21,21,20,20,20,20,20,20,20,20,19,19,19,19,19,19,19,19,19,19,18,18,18,18,
18,18,18,18,18,18,18,17,17,17,17,17,17,17,17,17,17,17,17,17,16,16,16,16,16,
16,16,16,16,16,16,16,16,16,16,16,15,15,15,15,15,15,15,15,15,15,15,15,15,15,
15,15,15,15,15,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,
14,14,14,14,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,
13,13,13,13,13,13,13,13,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,11,11,11,11,
11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,
11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,10,10,10,10,10,
10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,
10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,
10,10,10,10,10,10,10,10,10,10,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,
9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,
9
};

/* 拧动90度 */
static int ND90Ac[] = {
78,60,51,45,40,37,34,32,31,29,28,27,26,25,24,23,23,22,21,21,20,20,19,
19,19,18,18,18,17,17,17,17,16,16,16,16,15,15,15,15,15,14,14,14,14,14,14,14,
13,13,13,13,13,13,13,13,12,12,12,12,12,12,12,12,12,12,11,11,11,11,11,11,11,
11,11,11,11,11,11,11,11,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,
9,9,9,9,9,9,9,9,9,9,9
};

/* 拧动180度 */
static int ND180Ac[] = {
83,64,54,47,43,39,37,34,33,31,30,28,27,26,26,25,24,23,23,22,22,21,21,
20,20,20,19,19,18,18,18,18,17,17,17,17,16,16,16,16,16,15,15,15,15,15,15,14,
14,14,14,14,14,14,13,13,13,13,13,13,13,13,13,13,12,12,12,12,12,12,12,12,12,
12,12,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,10,10,10,10,10,10,10,10,
10,10,10,10,10,10,10,10,10,10,10,10,10,9,9,9,9,9,9,9,9,9,9,9,9,
9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,8,8,8,8,8,8,8,8,8,
8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,
8,8,8,8,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,
7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,
7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,6,6,6,6,6,6,6,6,6,6,
6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,
6,6,6,6,6
};

/* 带动90度 */
static int DD90Ac[] = {
91,80,73,67,62,58,55,53,50,48,46,45,43,42,41,40,39,38,37,36,35,
34,34,33,32,32,31,31,30,30,29,29,29,28,28,27,27,27,26,26,26,26,25,25,25,24,
24,24,24,24,23,23,23,23,22,22,22
};

/* 带动180度 */
static int DD180Ac[] = {
90,81,75,70,65,62,59,56,54,52,50,48,47,46,44,43,42,41,40,39,
38,38,37,36,36,35,34,34,33,33,32,32,32,31,31,30,30,30,29,29,29,28,28,28,27,
27,27,27,26,26,26,26,25,25,25,25,24,24,24,24,24,24,23,23,23,23,23,23,22,22,
22,22,22,22,22,21,21,21,21,21,21,21,20,20,20,20,20,20,20,20,20,19,19,19,19,
19,19,19,19,19,19,19,18,18,18,18,18,18,18,18,18,18,18,18,18,17,17,17,17,17,
17,17,17,17,17,17,17,17,17,16,16,16,16,16,16,16,16,16,16,16,16,16,16,16,16,
16,16,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,14,
14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,
13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,
13,13,13,13,13,13,13,13,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,
11
};

/* ========================================================
   原始电机旋转 (不更新robot状态, 用于收管等场景)
   motor_id: MOTOR_1 或 MOTOR_2
   total_steps: 脉冲总数
   dir: DIR_CW(正转) 或 DIR_CCW(反转)
   speed_5us: 匀速阶段延时 (单位 ×5us)
   accel_steps: 加减速步数
   ======================================================== */
static void RawRotate(int motor_id, int total_steps, int dir,
                      int speed_5us, int accel_steps)
{
    int i, d;
    int speed_start = speed_5us * 5;  /* 起步为匀速的5倍 */

    for (i = 0; i < total_steps; i++)
    {
        if (i < accel_steps)
            d = speed_start - (speed_start - speed_5us) * i / accel_steps;
        else if (i >= total_steps - accel_steps)
            d = speed_5us + (speed_start - speed_5us)
                * (i - (total_steps - accel_steps)) / accel_steps;
        else
            d = speed_5us;

        if (dir == DIR_CW)
        {
            if (motor_id == MOTOR_1) L_DIR_P; else R_DIR_P;
        }
        else
        {
            if (motor_id == MOTOR_1) L_DIR_N; else R_DIR_N;
        }

        if (motor_id == MOTOR_1)
        {
            L_PUL_UP;   cpu_delay_5us(d);
            L_PUL_DOWN; cpu_delay_5us(d);
        }
        else
        {
            R_PUL_UP;   cpu_delay_5us(d);
            R_PUL_DOWN; cpu_delay_5us(d);
        }
    }
}

/* ========================================================
   收管函数 — 张开手爪 → 反向旋转归零 → 恢复手爪
   motor_id: MOTOR_1 / MOTOR_2
   ======================================================== */
static void TubeUnwind(int motor_id)
{
    int8_t *winding;
    uint8_t saved_hand;
    int unwind_units;
    int unwind_dir;

    if (motor_id == MOTOR_1)
    {
        winding = &g_robot.LeftTubeWinding;
        saved_hand = g_robot.LeftHand;
        L_HAND_OPEN;
        g_robot.LeftHand = OPEN;
    }
    else
    {
        winding = &g_robot.RightTubeWinding;
        saved_hand = g_robot.RightHand;
        R_HAND_OPEN;
        g_robot.RightHand = OPEN;
    }

    cpu_delay_ms(OpenHand_TIM);

    unwind_units = ABS(*winding);
    unwind_dir   = (*winding > 0) ? DIR_CCW : DIR_CW;

    /* 空载收管, 速度可以快 */
    RawRotate(motor_id, unwind_units * (MotorSub / 4), unwind_dir, 5, 200);

    *winding = 0;

    /* 恢复手爪状态 */
    if (saved_hand == CLOSE)
    {
        if (motor_id == MOTOR_1)
        {
            L_HAND_CLOSE;
            g_robot.LeftHand = CLOSE;
        }
        else
        {
            R_HAND_CLOSE;
            g_robot.RightHand = CLOSE;
        }
        cpu_delay_ms(CloseHand_TIM);
    }
}

/* ========================================================
   左手运动函数
   ======================================================== */

static void MoveL1(int AcDelay[], uint16_t AcNum)
{
    int i;
    int totalPulse = MotorSub / 4;

    L_DIR_P;
    cpu_delay_5us(200);

    for (i = 0; i < AcNum; i++)
    {
        L_PUL_UP;
        cpu_delay_5us((int)(AcDelay[i]));
        L_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[i]));
    }

    for (i = AcNum; i < totalPulse - AcNum; i++)
    {
        L_PUL_UP;
        cpu_delay_5us(AcDelay[AcNum - 1]);
        L_PUL_DOWN;
        cpu_delay_5us(AcDelay[AcNum - 1]);
    }

    for (i = totalPulse - AcNum; i < totalPulse; i++)
    {
        L_PUL_UP;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
        L_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
    }
    g_robot.LeftDir += 1;
    g_robot.LeftTubeWinding += 1;
}

static void MoveL2(int AcDelay[], uint16_t AcNum)
{
    int i;
    int totalPulse = MotorSub / 2;

    /* 智能方向选择: 选使|winding|较小的方向, 避免缠管 */
    {
        int cw_winding  = g_robot.LeftTubeWinding + 2;
        int ccw_winding = g_robot.LeftTubeWinding - 2;

        if (ABS(cw_winding) <= ABS(ccw_winding))
        {
            L_DIR_P;
            g_robot.LeftTubeWinding = cw_winding;
        }
        else
        {
            L_DIR_N;
            g_robot.LeftTubeWinding = ccw_winding;
        }
    }
    cpu_delay_5us(200);

    for (i = 0; i < AcNum; i++)
    {
        L_PUL_UP;
        cpu_delay_5us((int)(AcDelay[i]));
        L_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[i]));
    }

    for (i = AcNum; i < totalPulse - AcNum; i++)
    {
        L_PUL_UP;
        cpu_delay_5us(AcDelay[AcNum - 1]);
        L_PUL_DOWN;
        cpu_delay_5us(AcDelay[AcNum - 1]);
    }

    for (i = totalPulse - AcNum; i < totalPulse; i++)
    {
        L_PUL_UP;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
        L_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
    }
    g_robot.LeftDir += 2;
}

static void MoveL3(int AcDelay[], uint16_t AcNum)
{
    int i;
    int totalPulse = MotorSub / 4;

    L_DIR_N;
    cpu_delay_5us(200);

    for (i = 0; i < AcNum; i++)
    {
        L_PUL_UP;
        cpu_delay_5us((int)(AcDelay[i]));
        L_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[i]));
    }

    for (i = AcNum; i < totalPulse - AcNum; i++)
    {
        L_PUL_UP;
        cpu_delay_5us(AcDelay[AcNum - 1]);
        L_PUL_DOWN;
        cpu_delay_5us(AcDelay[AcNum - 1]);
    }

    for (i = totalPulse - AcNum; i < totalPulse; i++)
    {
        L_PUL_UP;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
        L_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
    }
    g_robot.LeftDir += 3;
    g_robot.LeftTubeWinding -= 1;
}

/* ========================================================
   右手运动函数
   ======================================================== */

static void MoveR1(int AcDelay[], uint16_t AcNum)
{
    int i;
    int totalPulse = MotorSub / 4;

    R_DIR_P;
    cpu_delay_5us(200);

    for (i = 0; i < AcNum; i++)
    {
        R_PUL_UP;
        cpu_delay_5us((int)(AcDelay[i]));
        R_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[i]));
    }

    for (i = AcNum; i < totalPulse - AcNum; i++)
    {
        R_PUL_UP;
        cpu_delay_5us(AcDelay[AcNum - 1]);
        R_PUL_DOWN;
        cpu_delay_5us(AcDelay[AcNum - 1]);
    }

    for (i = totalPulse - AcNum; i < totalPulse; i++)
    {
        R_PUL_UP;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
        R_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
    }
    g_robot.RightDir += 1;
    g_robot.RightTubeWinding += 1;
}

static void MoveR2(int AcDelay[], uint16_t AcNum)
{
    int i;
    int totalPulse = MotorSub / 2;

    /* 智能方向选择 */
    {
        int cw_winding  = g_robot.RightTubeWinding + 2;
        int ccw_winding = g_robot.RightTubeWinding - 2;

        if (ABS(cw_winding) <= ABS(ccw_winding))
        {
            R_DIR_P;
            g_robot.RightTubeWinding = cw_winding;
        }
        else
        {
            R_DIR_N;
            g_robot.RightTubeWinding = ccw_winding;
        }
    }
    cpu_delay_5us(200);

    for (i = 0; i < AcNum; i++)
    {
        R_PUL_UP;
        cpu_delay_5us((int)(AcDelay[i]));
        R_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[i]));
    }

    for (i = AcNum; i < totalPulse - AcNum; i++)
    {
        R_PUL_UP;
        cpu_delay_5us(AcDelay[AcNum - 1]);
        R_PUL_DOWN;
        cpu_delay_5us(AcDelay[AcNum - 1]);
    }

    for (i = totalPulse - AcNum; i < totalPulse; i++)
    {
        R_PUL_UP;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
        R_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
    }
    g_robot.RightDir += 2;
}

static void MoveR3(int AcDelay[], uint16_t AcNum)
{
    int i;
    int totalPulse = MotorSub / 4;

    R_DIR_N;
    cpu_delay_5us(200);

    for (i = 0; i < AcNum; i++)
    {
        R_PUL_UP;
        cpu_delay_5us((int)(AcDelay[i]));
        R_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[i]));
    }

    for (i = AcNum; i < totalPulse - AcNum; i++)
    {
        R_PUL_UP;
        cpu_delay_5us(AcDelay[AcNum - 1]);
        R_PUL_DOWN;
        cpu_delay_5us(AcDelay[AcNum - 1]);
    }

    for (i = totalPulse - AcNum; i < totalPulse; i++)
    {
        R_PUL_UP;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
        R_PUL_DOWN;
        cpu_delay_5us((int)(AcDelay[totalPulse - i - 1]));
    }
    g_robot.RightDir += 3;
    g_robot.RightTubeWinding -= 1;
}

/* ========================================================
   MotorMove - 统一的机械动作执行函数
   ======================================================== */

void MotorMove(uint8_t MechStep)
{
    uint16_t AcNum = 0;
    int *AcDelay = NULL;

    /* --- 根据当前手爪状态和动作类型选择加减速曲线 --- */

    /* 空转90 */
    if ((((MechStep == L_1) || (MechStep == L_3)) && (g_robot.LeftHand  == OPEN)) ||
        (((MechStep == R_1) || (MechStep == R_3)) && (g_robot.RightHand == OPEN)))
    {
        AcNum   = sizeof(KZ90Ac) / sizeof(KZ90Ac[0]);
        AcDelay = KZ90Ac;
    }
    /* 空转180 */
    else if (((MechStep == L_2) && (g_robot.LeftHand  == OPEN)) ||
             ((MechStep == R_2) && (g_robot.RightHand == OPEN)))
    {
        AcNum   = sizeof(KZ180Ac) / sizeof(KZ180Ac[0]);
        AcDelay = KZ180Ac;
    }
    /* 拧动90 */
    else if (((MechStep == L_1) || (MechStep == L_3) || (MechStep == R_1) || (MechStep == R_3)) &&
             ((g_robot.RightHand == CLOSE) && (g_robot.LeftHand == CLOSE)))
    {
        AcNum   = sizeof(ND90Ac) / sizeof(ND90Ac[0]);
        AcDelay = ND90Ac;
    }
    /* 拧动180 */
    else if (((MechStep == L_2) || (MechStep == R_2)) &&
             ((g_robot.RightHand == CLOSE) && (g_robot.LeftHand == CLOSE)))
    {
        AcNum   = sizeof(ND180Ac) / sizeof(ND180Ac[0]);
        AcDelay = ND180Ac;
    }
    /* 带动90 */
    else if ((((MechStep == L_1) || (MechStep == L_3)) && ((g_robot.LeftHand  == CLOSE) && (g_robot.RightHand == OPEN))) ||
             (((MechStep == R_1) || (MechStep == R_3)) && ((g_robot.RightHand == CLOSE) && (g_robot.LeftHand  == OPEN))))
    {
        AcNum   = sizeof(DD90Ac) / sizeof(DD90Ac[0]);
        AcDelay = DD90Ac;
    }
    /* 带动180 */
    else if (((MechStep == L_2) && ((g_robot.LeftHand  == CLOSE) && (g_robot.RightHand == OPEN))) ||
             ((MechStep == R_2) && ((g_robot.RightHand == CLOSE) && (g_robot.LeftHand  == OPEN))))
    {
        AcNum   = sizeof(DD180Ac) / sizeof(DD180Ac[0]);
        AcDelay = DD180Ac;
    }

    /* --- 执行动作 (含气管缠绕检查) --- */
    switch (MechStep)
    {
        case L_C:
        {
            if (g_robot.LeftHand == CLOSE)
                break;
            g_robot.LeftHand = CLOSE;
            L_HAND_CLOSE;
            cpu_delay_ms(CloseHand_TIM);
            break;
        }
        case L_O:
        {
            if (g_robot.LeftHand == OPEN)
                break;
            g_robot.LeftHand = OPEN;
            L_HAND_OPEN;
            cpu_delay_ms(OpenHand_TIM);
            break;
        }
        case L_1:
            if (g_robot.LeftTubeWinding >= 3)
                TubeUnwind(MOTOR_1);
            MoveL1(AcDelay, AcNum);
            cpu_delay_ms(MotorMoveInterval_TIM);
            break;
        case L_2:
            /* L_2内部已做智能方向选择, 但若|winding|已达极限仍需收管 */
            if (ABS(g_robot.LeftTubeWinding) >= 3)
                TubeUnwind(MOTOR_1);
            MoveL2(AcDelay, AcNum);
            cpu_delay_ms(MotorMoveInterval_TIM);
            break;
        case L_3:
            if (g_robot.LeftTubeWinding <= -3)
                TubeUnwind(MOTOR_1);
            MoveL3(AcDelay, AcNum);
            cpu_delay_ms(MotorMoveInterval_TIM);
            break;

        case R_C:
        {
            if (g_robot.RightHand == CLOSE)
                break;
            g_robot.RightHand = CLOSE;
            R_HAND_CLOSE;
            cpu_delay_ms(CloseHand_TIM);
            break;
        }
        case R_O:
        {
            if (g_robot.RightHand == OPEN)
                break;
            g_robot.RightHand = OPEN;
            R_HAND_OPEN;
            cpu_delay_ms(OpenHand_TIM);
            break;
        }
        case R_1:
            if (g_robot.RightTubeWinding >= 3)
                TubeUnwind(MOTOR_2);
            MoveR1(AcDelay, AcNum);
            cpu_delay_ms(MotorMoveInterval_TIM);
            break;
        case R_2:
            if (ABS(g_robot.RightTubeWinding) >= 3)
                TubeUnwind(MOTOR_2);
            MoveR2(AcDelay, AcNum);
            cpu_delay_ms(MotorMoveInterval_TIM);
            break;
        case R_3:
            if (g_robot.RightTubeWinding <= -3)
                TubeUnwind(MOTOR_2);
            MoveR3(AcDelay, AcNum);
            cpu_delay_ms(MotorMoveInterval_TIM);
            break;

        default: break;
    }
}

/* ========================================================
   ResetHandDir - 解魔方完成后复位手爪位置
   ======================================================== */

void ResetHandDir(void)
{
    g_robot.LeftDir  %= 4;
    g_robot.RightDir %= 4;

    if (g_robot.LeftDir == 1)
    {
        MotorMove(L_O);
        MotorMove(L_3);
        MotorMove(L_C);
    }
    if (g_robot.LeftDir == 3)
    {
        MotorMove(L_O);
        MotorMove(L_1);
        MotorMove(L_C);
    }
    if (g_robot.RightDir == 1)
    {
        MotorMove(R_O);
        MotorMove(R_3);
        MotorMove(R_C);
    }
    if (g_robot.RightDir == 3)
    {
        MotorMove(R_O);
        MotorMove(R_1);
        MotorMove(R_C);
    }
    if (g_robot.LeftDir == 2)
    {
        MotorMove(L_O);
        MotorMove(L_2);
        MotorMove(L_C);
    }
    if (g_robot.RightDir == 2)
    {
        MotorMove(R_O);
        MotorMove(R_2);
        MotorMove(R_C);
    }

    /* 解算完成, 清零缠绕计数 */
    g_robot.LeftTubeWinding  = 0;
    g_robot.RightTubeWinding = 0;
}
