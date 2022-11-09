# SJ-201 Interface
Contains Python bindings for released versions of the SJ201 using 
[Mycroft testing code](https://github.com/MycroftAI/mark-ii-hardware-testing)
for reference.

# CLI Usage

## `sj201 get-revision`
Get a string representation of the detected SJ201 board (`6` or `10`) or `0`

## `sj201 reset-led <color>`
Chase the specified color and then chase off LED ring. Valid colors are:
- white
- yellow
- red
- green
- blue
- magenta
- burnt_orange
- mycroft_red
- mycroft_green
- mycroft_blue
>*NOTE*: On the SJ201R10, this command must be run as root

## `sj201 set-fan-speed <percent>`
Set the fan speed to the specified speed as a percentage.
>*NOTE*: On the SJ201R10, changing the fan speed is currently not persistent and
> the fan will default to 100% after momentarily setting the requested speed.
> Setting speed to 0 will turn off the fan until the Raspberry Pi is shut down,
> at which point the fan will resume 100%.

## `sj201 init-ti-amp`
Perform boot time initialization of the TAS5806 Audio Amplifier

## `sj201 patch-config-txt`
Perform one-time update of config.txt for detected SJ201 hardware.
>*NOTE*: Applying this could cause damage or unexpected behavior for connected
> HATs/GPIO components.

>*NOTE*: `reboot` will cause kernel panics unless power is physically disconnected
