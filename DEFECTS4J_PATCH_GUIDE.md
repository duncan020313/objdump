# Defects4J Build File Patching Guide

## 개요

이 가이드는 Defects4J 프로젝트에서 발생할 수 있는 컴파일 문제를 해결하기 위한 자동 패치 시스템을 설명합니다.

## 문제 배경

### 발생했던 컴파일 에러

Chart 프로젝트를 빌드할 때 다음과 같은 문제가 발생했습니다:

1. **Jackson 라이브러리 누락**: 
   - Jackson JAR 파일들이 `lib/` 디렉토리에는 존재하지만 `build.xml`의 classpath에 포함되지 않음
   - 결과: `package com.fasterxml.jackson.databind does not exist` 에러 발생

2. **컴파일 대상 제외**:
   - `org/instrument/**` 패키지가 javac의 include 패턴에서 제외됨
   - 결과: `DebugDump.java` 등의 파일이 컴파일되지 않음

## 해결 방안

### 1. 공유 빌드 파일 패치

기본 Defects4J 공유 빌드 파일을 패치합니다:

```bash
cd /root/objdump
python3 setup_defects4j.py
```

이 명령은 `/defects4j/framework/projects/defects4j.build.xml`을 패치하여 Jackson 의존성을 추가합니다.

### 2. 프로젝트별 빌드 파일 패치

모든 프로젝트별 템플릿 빌드 파일을 자동으로 패치합니다:

```bash
python3 setup_defects4j.py --patch-projects
```

이 명령은 다음 프로젝트들의 빌드 파일을 패치합니다:
- Chart, Closure, Cli, Codec, Collections, Compress, Csv
- Gson, JacksonCore, JacksonDatabind, JacksonXml
- Jsoup, JxPath, Lang, Math, Mockito, Time

### 3. 전체 패치 (권장)

공유 빌드 파일과 프로젝트 빌드 파일을 모두 패치합니다:

```bash
python3 setup_defects4j.py --patch-projects
```

## 패치 내용

### 1. Jackson 속성 추가

```xml
<!-- Jackson dependencies for instrumentation -->
<property name="jackson.version" value="2.13.0" />
<property name="jackson.core.jar" value="${d4j.workdir}/lib/jackson-core-${jackson.version}.jar" />
<property name="jackson.databind.jar" value="${d4j.workdir}/lib/jackson-databind-${jackson.version}.jar" />
<property name="jackson.annotations.jar" value="${d4j.workdir}/lib/jackson-annotations-${jackson.version}.jar" />
```

### 2. build.classpath 오버라이드

기존 `ant/build.xml`의 `build.classpath`를 오버라이드하여 Jackson 라이브러리를 포함합니다:

```xml
<!-- Override build.classpath to include Jackson libraries -->
<path id="build.classpath">
    <pathelement location="${servlet.jar}"/>
    <pathelement location="${jackson.core.jar}"/>
    <pathelement location="${jackson.databind.jar}"/>
    <pathelement location="${jackson.annotations.jar}"/>
</path>
```

### 3. javac 태스크에 org/instrument/** 패턴과 nowarn 속성 추가

```xml
<javac srcdir="${d4j.workdir}/source" 
       destdir="${d4j.workdir}/build" 
       ...
       nowarn="true">  <!-- 추가됨 -->
    <classpath refid="build.classpath" />
    <include name="org/jfree/**" />
    <include name="org/instrument/**" />  <!-- 추가됨 -->
</javac>
```

### 중요 사항: XML 주석 보존

⚠️ **경고**: 자동 패치 스크립트는 Python의 `xml.etree.ElementTree`를 사용하므로 **XML 주석과 포맷팅을 보존하지 못합니다**.

- **Chart.build.xml**은 라이선스 헤더를 보존하기 위해 **수동으로 패치되었습니다**
- 다른 프로젝트의 빌드 파일에도 중요한 라이선스 헤더가 있을 수 있습니다
- 자동 패치 후에는 반드시 git diff로 변경사항을 확인하세요

**권장 사항**:
1. 자동 패치 전에 백업 생성: `cp file.xml file.xml.backup`
2. 패치 후 git diff로 변경사항 확인
3. 라이선스 헤더가 손실된 경우 수동으로 복구
4. Chart 프로젝트는 이미 수동 패치되었으므로 재패치 불필요

## 스크립트 옵션

### setup_defects4j.py

```bash
# 기본 사용법
python3 setup_defects4j.py [OPTIONS]

# 옵션
--verify            # 현재 설정 확인만 수행
--rollback          # 원본 파일로 복원
--force             # 이미 패치된 경우에도 강제로 재패치
--patch-projects    # 프로젝트별 빌드 파일도 패치
```

### 사용 예시

```bash
# 1. 현재 설정 확인
python3 setup_defects4j.py --verify

# 2. 공유 빌드 파일만 패치
python3 setup_defects4j.py

# 3. 프로젝트 빌드 파일만 패치
python3 setup_defects4j.py --patch-projects

# 4. 강제로 모든 파일 재패치
python3 setup_defects4j.py --force --patch-projects

# 5. 원본으로 복원
python3 setup_defects4j.py --rollback
```

## 기술적 세부사항

### 패치 프로세스

1. **XML 파싱**: `xml.etree.ElementTree`를 사용하여 빌드 파일 파싱
2. **속성 추가**: Jackson 버전 및 JAR 경로 속성 추가
3. **Classpath 업데이트**: `build.classpath` 또는 `compile.classpath`에 Jackson 라이브러리 추가
4. **Javac 수정**: compile 타겟의 javac 태스크에 `org/instrument/**` include 패턴 추가
5. **XML 포맷팅**: 적절한 들여쓰기를 적용하여 가독성 향상

### 모듈 구조

```
objdump/
├── setup_defects4j.py           # 메인 패치 스크립트
├── build_systems/
│   └── ant.py                   # Ant 빌드 파일 처리 로직
│       ├── _indent_xml()        # XML 포맷팅
│       ├── _process_build_file()      # 빌드 파일 처리
│       ├── _ensure_properties()       # 속성 추가
│       ├── _add_pathelements_to_classpath()  # Classpath 업데이트
│       ├── _fix_compile_target_javac()       # Javac 수정
│       ├── add_jackson_to_build_file()       # 개별 빌드 파일 패치
│       └── add_jackson_to_project_template() # 프로젝트 템플릿 패치
└── defects4j.py                 # Defects4J 유틸리티 함수
```

## 백업 및 복원

### 자동 백업

스크립트는 수정 전에 자동으로 백업을 생성합니다:
- 백업 위치: `<원본파일>.backup`
- 예: `/defects4j/framework/projects/defects4j.build.xml.backup`

### 복원 방법

```bash
# 자동 복원
python3 setup_defects4j.py --rollback

# 수동 복원 (필요시)
cp /defects4j/framework/projects/defects4j.build.xml.backup \
   /defects4j/framework/projects/defects4j.build.xml
```

## 문제 해결

### 컴파일이 여전히 실패하는 경우

1. **Jackson JAR 파일 확인**:
   ```bash
   ls -la /tmp/objdump-d4j/chart-1/lib/jackson-*.jar
   ```

2. **build.xml 확인**:
   ```bash
   grep -A 5 "build.classpath" /defects4j/framework/projects/Chart/Chart.build.xml
   ```

3. **org/instrument 패턴 확인**:
   ```bash
   grep "org/instrument" /defects4j/framework/projects/Chart/Chart.build.xml
   ```

4. **강제 재패치**:
   ```bash
   python3 setup_defects4j.py --force --patch-projects
   ```

### XML 파싱 에러

XML 파일이 손상된 경우:

1. 백업에서 복원:
   ```bash
   python3 setup_defects4j.py --rollback
   ```

2. 수동으로 XML 유효성 검사:
   ```bash
   xmllint --noout /defects4j/framework/projects/Chart/Chart.build.xml
   ```

## 권장 사항

1. **정기적인 백업**: 중요한 빌드 파일은 별도로 백업
2. **점진적 패치**: 먼저 테스트 프로젝트로 검증 후 전체 적용
3. **버전 관리**: Git 등으로 빌드 파일 변경사항 추적

## 참고

- 이 패치는 Defects4J 2.0 기준으로 작성되었습니다
- Jackson 버전은 2.13.0을 기본으로 사용합니다
- 다른 버전이 필요한 경우 스크립트의 `JACKSON_VERSION` 변수를 수정하세요

