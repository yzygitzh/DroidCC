root_path=/home/yzy/humanoid/
humanoid_server=162.105.87.223:50405

out_tester=_humanoid

tested=`ls $root_path/out$out_tester/$1/finish_mark`

if [ -z "$tested" ]; then
    rm -rf $root_path/out$out_tester/$1
    mkdir -p $root_path/out$out_tester/$1

    qemu-img create -f qcow2 $root_path/qemu/droidbot-6.0-r3.qcow2.$2 -o backing_file=$root_path/qemu/droidbot-6.0-r3.qcow2

    qemu-system-i386 -drive file=$root_path/qemu/droidbot-6.0-r3.qcow2.$2,if=virtio -m 2048 -smp cpus=4 -enable-kvm -machine q35 -nographic -net nic,model=e1000 -net user,hostfwd=tcp::$2-:5555 &
    qemu_pid=$!

    sleep 60
    adb connect localhost:$2

    # Extract class-methods in apk
    unzip $root_path/apps/$1.apk -d /tmp/extract_class_methods_$2
    for dex_path in /tmp/extract_class_methods_$2/*.dex; do
        ./extract_class_methods $dex_path > $dex_path.extracted_class_method
    done
    cat /tmp/extract_class_methods_$2/*.extracted_class_method | sort | uniq > /tmp/extract_class_methods_$2/redroid_filters
    adb -s localhost:$2 push /tmp/extract_class_methods_$2/redroid_filters /data/local/tmp/
    rm -rf /tmp/extract_class_methods_$2

    # Run Humanoid
    timeout 4000s droidbot -d localhost:$2 -a $root_path/apps/$1.apk -interval 5 -count 2000 -policy dfs_greedy -grant_perm -keep_env -keep_app -random -ignore_ad -is_emulator -humanoid $humanoid_server -use_method_profiling full -o $root_path/out$out_tester/$1/droidbot_out &> $root_path/out$out_tester/$1/droidbot.log &

    tester_pid=$!

    while kill -0 "$tester_pid" > /dev/null 2>&1; do
        sleep 1
    done

    # Remove unfinished one
    rm -rf $root_path/out$out_tester/$1/droidbot_out/temp

    adb -s localhost:$2 shell dumpsys activity activities | grep 'Hist #' >> $root_path/out$out_tester/$1/finish_mark
    while kill -0 "$qemu_pid" > /dev/null 2>&1; do
        sleep 1
        kill -9 $qemu_pid
    done

else
    echo "PASS $1"
fi
