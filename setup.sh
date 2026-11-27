#!/usr/bin/env bash
set -euo pipefail

export ANDROID_NDK_HOME="${ANDROID_NDK_HOME:-$HOME/Android/Sdk/ndk/27.0.12077973}"
export MESON_WORKING_DIR="$PWD"
NDK_SYSROOT="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/sysroot"
# Bindgen usa uma variavel especifica para o target e pode nao aplicar a generica.
# Forca os headers Android para evitar que libclang caia nos headers glibc do runner.
export BINDGEN_EXTRA_CLANG_ARGS="--sysroot=$NDK_SYSROOT -isystem $NDK_SYSROOT/usr/include -isystem $NDK_SYSROOT/usr/include/aarch64-linux-android"
export BINDGEN_EXTRA_CLANG_ARGS_aarch64_linux_android="$BINDGEN_EXTRA_CLANG_ARGS"
export BINDGEN_EXTRA_CLANG_ARGS_AARCH64_LINUX_ANDROID="$BINDGEN_EXTRA_CLANG_ARGS"

if [[ ! -x "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-ar" ]]; then
  echo "NDK nao encontrado ou incompleto: $ANDROID_NDK_HOME" >&2
  exit 1
fi

# Build dos utilitarios nativos (host), necessarios na compilacao cruzada Android.
# Estas opcoes seguem a configuracao documentada pelo Mesa para cross-builds Panfrost.
rm -rf build-host
meson setup build-host \
  -Dplatforms=x11 \
  -Dglx=disabled \
  -Degl=disabled \
  -Dgbm=disabled \
  -Dopengl=false \
  -Dgles1=disabled \
  -Dgles2=disabled \
  -Dtools=panfrost \
  -Dgallium-drivers=panfrost \
  -Dvulkan-drivers= \
  -Dmesa-clc=enabled \
  -Dinstall-mesa-clc=true \
  -Dprecomp-compiler=enabled \
  -Dinstall-precomp-compiler=true \
  -Dllvm=enabled

ninja -C build-host \
  src/compiler/clc/mesa_clc \
  src/compiler/spirv/vtn_bindgen2 \
  src/panfrost/clc/panfrost_compile

# Confirma os binarios antes de continuar; evita mascarar falhas do build-host.
for tool in \
  build-host/src/compiler/clc/mesa_clc \
  build-host/src/compiler/spirv/vtn_bindgen2 \
  build-host/src/panfrost/clc/panfrost_compile; do
  if [[ ! -x "$tool" ]]; then
    echo "Ferramenta nativa nao foi gerada: $tool" >&2
    exit 1
  fi
done

# Alguns pontos do build procuram os nomes com hifen; mantenha os nomes originais tambem.
ln -sfn "$MESON_WORKING_DIR/build-host/src/compiler/clc/mesa_clc" \
  "$MESON_WORKING_DIR/build-host/src/compiler/clc/mesa-clc"
ln -sfn "$MESON_WORKING_DIR/build-host/src/compiler/spirv/vtn_bindgen2" \
  "$MESON_WORKING_DIR/build-host/src/compiler/spirv/vtn-bindgen2"
ln -sfn "$MESON_WORKING_DIR/build-host/src/panfrost/clc/panfrost_compile" \
  "$MESON_WORKING_DIR/build-host/src/panfrost/clc/panfrost-compile"

export PATH="$MESON_WORKING_DIR/build-host/src/compiler/clc:$MESON_WORKING_DIR/build-host/src/compiler/spirv:$MESON_WORKING_DIR/build-host/src/panfrost/clc:$PATH"

mkdir -p shims/include
"$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-ar" cr shims/librt.a
export PKG_CONFIG_LIBDIR="$MESON_WORKING_DIR/shims"

cat > shims/xrandr.pc <<'PC'
Name: xrandr
Description: xrandr
Version: 1.15
Libs: -lXrandr
Cflags:
PC

cat > shims/libx11-xcb.pc <<'PC'
Name: libx11-xcb
Description: libx11-xcb
Version: 2.5
Libs: -lX11-xcb
Cflags:
PC

cat > shims/android.hardware.graphics.mapper.pc <<'PC'
Name: android.hardware.graphics.mapper
Description: android.hardware.graphics.mapper
Version: 4.0
Libs: -landroid.hardware.graphics.mapper
Cflags:
PC

for lib in xcb xcb-randr xcb-dri3 xcb-present xcb-shm xcb-sync xshmfence xcb-xfixes gralloctypes hidlbase utils cutils hardware log sync nativewindow ui; do
  cat > "shims/$lib.pc" <<PC
Name: $lib
Description: $lib
Version: 1.15
Libs: -l$lib
Cflags:
PC
done

if [[ ! -f android.toml ]]; then
  echo "Arquivo android.toml nao encontrado na raiz do repositorio" >&2
  exit 1
fi
# Isola o pkg-config Android das bibliotecas instaladas no host.
unset PKG_CONFIG_PATH

envsubst < android.toml > /tmp/android_wrapper.toml

MESON_ARGS=(
  --cross-file /tmp/android_wrapper.toml
  -Dbuildtype=debug
  -Dplatforms=android
  -Dandroid-stub=true
  -Dandroid-libbacktrace=disabled
  -Dplatform-sdk-version=31
  -Dglx=disabled
  -Dgbm=disabled
  -Degl=disabled
  -Dopengl=false
  -Dgles1=disabled
  -Dgles2=disabled
  -Dglvnd=disabled
  -Dvalgrind=disabled
  -Dgallium-drivers=
  -Dshared-glapi=disabled
  -Dzstd=disabled
  -Dmesa-clc=system
  -Dprecomp-compiler=system
  -Dvulkan-drivers=panfrost
  -Dllvm=disabled
  -Dstrip=false
  -Dpanfrost-kmds=kbase,panthor
  -Dpanfrost-rust=false
  -Dallow-fallback-for=libdrm \
  --force-fallback-for=libdrm,zlib,expat
  -Dlibdrm:default_library=static
  -Dzlib:default_library=static
  -Dexpat:default_library=static
)

if [[ -d build ]]; then
  meson setup build --reconfigure "${MESON_ARGS[@]}"
else
  meson setup build "${MESON_ARGS[@]}"
fi
