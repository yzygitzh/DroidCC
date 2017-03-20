# DroidCC

## Introduction

[PERUIM][PERUIM] gives an Android app's mapping from UI elements to permission requests by collecting method traces at runtime and finding relevant permissions using [pscout][pscout]. Based on that one can understand permissions more easily. Also, fine-grained UI-based permission control becomes possible. DroidCC is a proof-of-concepts implementation based on AOSP branch `android-6.0.1_r77`.

## Overview

DroidCC contains a system app and several system services.

### DroidCC App

The app is responsible for communicating with the **Rule service**, passing user-defined permission policies to it.

### DroidCC Services

1. Data Structures

    All the following data structures can be accessed by only one thread simultaneously at any time.

    * PERUIM rules

        The rules consist of user-defined permission control rules, coming in tri-tuples:

            <UI_identification, permission, allow/deny>

        The rules are maintained by DroidCC app and Rule service.

    * Permission Binding List

        The list consist of threads that combined to a certain PERUIM rule. All the permission requests from these threads should obey the PERUIM rule they've bound to. The binding list consists of dual-tuples like:

            <permission_request_feature, user-defined-rule>

        The list is maintained by DroidCC Perm service.

    * Accessibility Event Queue

        This queue records relevant accessibility events, containing view_click related ones, back button and so on. Normally this queue contains at most one event. If there is no element in the queue (cancelled by certain accessibility event), all permission requests are checked normally.

        The queue is maintained by Accessibility service.

    * Activity Event Queue

        This queue maintains the top activity record in order to identify a permission request's source. Normally this queue contains at most two activities (start_state to end_state).

        The queue is maintained by Activity service.

2. Rule Service

    This service maintains PERUIM rules and the permission binding list. It accepts bindings from DroidCC app in order to modify the PERUIM rules.

3. Perm Service

    The `checkPermission` implementation in Android framework is modified so that it will bind Perm service for another check after the regular one. This service checks accessibility queue and activity queue in order to get proper key to search in PERUIM rules.

4. Accessibility Service

    A child class of `AccessibilityService`. Maintain accessibility queue.

5. Activity Service

    The `ActivityManager` implementation in Android framework is modified so that it will bind Activity Service when new activity is pushed into the stack. Maintain activity queue.

[PERUIM]: http://sei.pku.edu.cn/~yaoguo/papers/Li-UbiComp-16.pdf
[pscout]: http://pscout.csl.toronto.edu