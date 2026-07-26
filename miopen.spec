# MIOpen — AMD deep learning primitives (TheRock 7.14)

Name:		miopen
Version:	7.14.0
Release:	1
Summary:	AMD ROCm deep learning primitive library
License:	MIT
Group:		System/Libraries
URL:		https://github.com/ROCm/rocm-libraries
Source0:	https://github.com/ROCm/rocm-libraries/releases/download/therock-7.14/miopen.tar.gz#/miopen-%{version}.tar.gz
# System clang (no $ROCM_PATH/lib/llvm/bin on FHS distros)
Patch0:		0001-clang-toolchain-system-llvm.patch

# HIP/device build yields empty debugsource; skip empty debuginfo packages
%global debug_package %{nil}

BuildRequires:	rocm-rpm-macros
BuildRequires:	cmake
BuildRequires:	ninja
BuildRequires:	rocm-cmake
BuildRequires:	hipcc
BuildRequires:	rocminfo
BuildRequires:	clang-tools
BuildRequires:	rocm-hip-devel
BuildRequires:	clang >= %{rocm_llvm_maj_ver}
BuildRequires:	rocblas-devel
BuildRequires:	hipblas-devel
BuildRequires:	hipblaslt-devel
BuildRequires:	rocrand-devel
BuildRequires:	pkgconfig(sqlite3)
BuildRequires:	pkgconfig(bzip2)
BuildRequires:	half-devel
BuildRequires:	boost-devel
BuildRequires:	nlohmann_json-devel
BuildRequires:	python3

ExclusiveArch:	%{x86_64} %{aarch64}

%description
MIOpen provides optimized deep learning primitives (convolutions, pooling,
normalization, …) for AMD GPUs via HIP. Built with full %%rocm_gpu_targets
(including gfx803 Polaris solution DBs); hipBLASLt GEMM path is used when
available (RDNA3/4), otherwise rocBLAS.

%package devel
Summary:	Development files for MIOpen
Group:		Development/C++
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires:	rocm-hip-devel
Provides:	miopen-devel = %{EVRD}

%description devel
Headers and CMake package for MIOpen.

%prep
%autosetup -n miopen -p1

%build
export CXX=clang++
export HIPCXX=clang
export CC=clang
export ROCM_PATH=%{_prefix}
export HIP_PATH=%{_prefix}
export HIP_DEVICE_LIB_PATH=%{_libdir}/amdgcn/bitcode
CXXFLAGS=$(printf '%s' "%{optflags}" | sed -E 's/-mfpmath=[^ ]+//g; s/ -m[a-z0-9+.=]+//g')
export CXXFLAGS="$CXXFLAGS -Wno-error=#warnings -Wno-#warnings"
export CFLAGS="$CXXFLAGS"
export LDFLAGS=$(printf '%s' "%{?__global_ldflags}" | sed -E 's/-mfpmath=[^ ]+//g; s/ -m[a-z0-9+.=]+//g')

%cmake %{rocm_cmake_fhs} %{rocm_cmake_gpu_targets} \
	-DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_CXX_COMPILER=clang++ \
	-DCMAKE_HIP_FLAGS="%{rocm_hip_clang_flags}" \
	-DCMAKE_CXX_FLAGS="$CXXFLAGS" \
	-DMIOPEN_BACKEND=HIP \
	-DBUILD_SHARED_LIBS=ON \
	-DMIOPEN_USE_COMPOSABLEKERNEL=OFF \
	-DMIOPEN_USE_MLIR=OFF \
	-DMIOPEN_USE_HIPBLASLT=ON \
	-DMIOPEN_BUILD_DRIVER=OFF \
	-DBUILD_TESTING=OFF \
	-DROCM_PATH=%{_prefix} \
	-DCMAKE_PREFIX_PATH=%{_prefix} \
	-G Ninja
# The cmake macro already chdirs into the build subdirectory
%ninja_build

%install
cd build
DESTDIR=%{buildroot} /usr/bin/ninja install -j%{?_smp_build_ncpus}%{!?_smp_build_ncpus:8}
cd ..
if [ -d %{buildroot}/usr/lib/cmake/miopen ] && [ ! -d %{buildroot}%{_libdir}/cmake/miopen ]; then
	mkdir -p %{buildroot}%{_libdir}/cmake
	mv %{buildroot}/usr/lib/cmake/miopen %{buildroot}%{_libdir}/cmake/
	rmdir %{buildroot}/usr/lib/cmake 2>/dev/null || true
	rmdir %{buildroot}/usr/lib 2>/dev/null || true
fi

%files
%license LICENSE.md
%doc README.md
%{_libdir}/libMIOpen.so.*
%{_datadir}/miopen/
%{_libexecdir}/miopen/
# upstream also drops a license copy under doc/miopen-hip
%{_docdir}/miopen-hip/

%files devel
%{_includedir}/miopen/
# FunctionalPlus headers/cmake vendored by MIOpen for AI kernel tuning
%{_includedir}/fplus/
%{_libdir}/cmake/FunctionalPlus/
%{_libdir}/libMIOpen.so
%{_libdir}/cmake/miopen/
