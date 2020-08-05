if [ "$(uname -s)" == "Linux" ]; then
    echo red
elif [ "$(uname -s)" == "CYGWIN" ]; then
    echo hi
fi
