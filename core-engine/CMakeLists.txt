cmake_minimum_required(VERSION 3.20)
project(SearchXCore VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
    add_compile_options(/W4 /WX-)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Core engine library
add_library(searchx_core STATIC
    src/inverted_index.cpp
    src/ranking.cpp
)

target_include_directories(searchx_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Enable testing
enable_testing()

# Document model & token contract test
add_executable(test_document tests/test_document.cpp)
target_link_libraries(test_document PRIVATE searchx_core)
add_test(NAME test_document COMMAND test_document)

# Inverted index unit tests
add_executable(test_inverted_index tests/test_inverted_index.cpp)
target_link_libraries(test_inverted_index PRIVATE searchx_core)
add_test(NAME test_inverted_index COMMAND test_inverted_index)

# Retrieval and ranking unit tests (TF-IDF & BM25)
add_executable(test_ranking tests/test_ranking.cpp)
target_link_libraries(test_ranking PRIVATE searchx_core)
add_test(NAME test_ranking COMMAND test_ranking)
