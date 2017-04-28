#!/bin/sh

FRAMEWORK_BASE="/mnt/data/aosp-latest/aosp/frameworks/base"
SEPOLICY="/mnt/data/aosp-latest/aosp/external/sepolicy"
PATCH_DIR="/home/yzy/2017_spring/DroidCC/marshmallow_patches"

gen_patch () {
	cd $1
	git checkout android-6.0.1_r77
	git checkout -b access_control_patch
	git merge android-6.0.1_r77_access_control --squash
	git add -all .
	git commit -m "access control patch"
	git format-patch android-6.0.1_r77
	git checkout android-6.0.1_r77_access_control
	git branch -D access_control_patch
	mv 000* "$PATCH_DIR/access_control_$2.patch"
}

gen_patch $FRAMEWORK_BASE "framework_base"
gen_patch $SEPOLICY "external_sepolicy"
