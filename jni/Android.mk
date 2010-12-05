LOCAL_PATH := $(call my-dir)

BUILD_PATH := $(LOCAL_PATH)/$(SCONS_BUILD_ROOT)

include $(CLEAR_VARS)

LOCAL_LDLIBS := -llog -lGLESv1_CM
LOCAL_MODULE    := glbuffer
LOCAL_SRC_FILES := glbuffer.c register_natives.c

include $(BUILD_SHARED_LIBRARY)
