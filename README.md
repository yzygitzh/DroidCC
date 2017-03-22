# DroidCC

## Introduction

[PERUIM][PERUIM] gives an Android app's mapping from UI elements to permission requests by collecting method traces at runtime and finding relevant permissions using [pscout][pscout]. Based on that one can understand permissions more easily. Also, fine-grained UI-based permission control becomes possible. DroidCC is a proof-of-concepts implementation based on AOSP branch `android-6.0.1_r77`.

## Overview

DroidCC contains a system app a system service.

### DroidCC App

The app is responsible for communicating with the **Rule service**, passing user-defined permission policies to it.

### DroidCC Service

1. Data Structures

    The data structures are stored in the DroidCC service class. They're maintained by different sources through calls of `getSystemService`.

    * PERUIM rules

        The rules consist of user-defined permission control rules, coming in quad-tuples:

            <UI_identification, permission_request_context, permission_id, allow/deny>

        UI_identification is a tri-tuple like:

            <start_activity, related_view, end_activity>

        permission_request_context contains the stack trace of the permission request, for further tuning. Theses rules can be modified by DroidCC app, and a initially given by PERUIM analysis (DroidBot and FlowDroid).

        1. User **Click/Swipe/Back** Button
        2. In View related method, check start_activity, pass it to the DroidCC service
        3. Check the view event, pass it to the DroidCC service
        4. (Some permission requests)
        5. (New activity entered. Set it as end_activity)
        6. (Some permission requests)

    * View Event Queue

        This queue records relevant view events, containing view_click related ones, back button and so on. Normally this queue contains at most one event. If there is no element in the queue, all permission requests are checked normally. The queue can be modified by instrument code around View methods.

    * Activity Event Queue

        This queue maintains the top activity record in order to identify a permission request's source. Normally this queue contains at most two activities (start_state to end_state). The queue can be modified by instrument code around ActivityManager methods.

2. Service Implementation

    This service maintains PERUIM rules and View/Activity queues, as well as does dynamic permission check. The `checkPermission` implementation in Android framework is modified so that it will call DroidCC service for another check after the regular one. This service checks view&activity queues in order to get proper key to search in PERUIM rules.

[PERUIM]: http://sei.pku.edu.cn/~yaoguo/papers/Li-UbiComp-16.pdf
[pscout]: http://pscout.csl.toronto.edu