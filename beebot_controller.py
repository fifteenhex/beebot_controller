#!/usr/bin/env python3

from sbus import sbus, utils
from tinyodrive import tinyodrive
import asyncio

ARM_CHAN = 5
REV_CHAN = 4


async def main():
    sb = await sbus.SBUSReceiver.create("/dev/ttyUSB1")
    od = await tinyodrive.TinyOdrive.create("/dev/ttyUSB0")

    armed = False
    reverse = False

    while True:
        frame: sbus.SBUSReceiver.SBUSFrame = await sb.get_frame()
        # print(frame)
        arm = frame.get_rx_channel(ARM_CHAN)

        if utils.channel_to_bool(arm):
            if not armed:
                armed = True
                print("armed")

            rev = utils.channel_to_bool(frame.get_rx_channel(REV_CHAN))
            if rev and not reverse:
                print("rev")
            elif not rev and reverse:
                print("forward")

            max_velocity = 60
            steering_velocity = 40
            throttle = utils.channel_to_float_linear(frame.get_rx_channel(utils.CHANNEL_THROTTLE))
            rudder = utils.channel_to_deflection(frame.get_rx_channel(utils.CHANNEL_RUDDER))
            split_rudder = utils.mixer_steering(rudder)
            velocity_left = (max_velocity * throttle) + (steering_velocity * split_rudder[0])
            velocity_right = (max_velocity * throttle) + (steering_velocity * split_rudder[1])
            # print(throttle, rudder, velocity_left, velocity_right)
            if rev:
                await od.set_velocity(0, -velocity_left)
                await od.set_velocity(1, velocity_right)
            else:
                await od.set_velocity(0, velocity_left)
                await od.set_velocity(1, -velocity_right)

            reverse = rev
        else:
            if armed:
                armed = False
                print("disarmed")

            await od.set_velocity(0, 0)
            await od.set_velocity(1, 0)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
