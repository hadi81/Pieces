import re

# Your DOT label (shortened for readability but still realistic)
label = """
Node0x56a55d0816b0 [shape=record,color=black,label="{IntraPHIVFGNode ID: 28300 PAGNode: [39242 = PHI(39264, )]    ; Function Attrs: noinline nounwind optnone\ndefine dso_local i32 @ai_network_create(ptr noundef %0, ptr noundef %1) #0 !dbg !31942 \{\n  %3 = alloca %struct.ai_error_, align 4\n  %4 = alloca ptr, align 4\n  %5 = alloca ptr, align 4\n  store ptr %0, ptr %4, align 4\n  call void @llvm.dbg.declare(metadata ptr %4, metadata !31947, metadata !DIExpression()), !dbg !31948\n  store ptr %1, ptr %5, align 4\n  call void @llvm.dbg.declare(metadata ptr %5, metadata !31949, metadata !DIExpression()), !dbg !31950\n  %6 = load ptr, ptr %4, align 4, !dbg !31951\n  %7 = load ptr, ptr %5, align 4, !dbg !31952\n  %8 = call i32 @ai_platform_network_create(ptr noundef %6, ptr noundef %7, ptr noundef @global_network, i8 noundef zeroext 1, i8 noundef zeroext 5, i8 noundef zeroext 0), !dbg !31953\n  %9 = getelementptr inbounds %struct.ai_error_, ptr %3, i32 0, i32 0, !dbg !31953\n  store i32 %8, ptr %9, align 4, !dbg !31953\n  %10 = getelementptr inbounds %struct.ai_error_, ptr %3, i32 0, i32 0, !dbg !31954\n  %11 = load i32, ptr %10, align 4, !dbg !31954\n  ret i32 %11, !dbg !31954\n\}\n \{ \"ln\": 503, \"file\": \"../X-CUBE-AI/App/network.c\" \}}"];

"""

def extract_called_functions(label):
    # Extract function names after "call" and before "("
    pattern = r'call\s+[^@]*@([^(]+)'
    return re.findall(pattern, label)

# Run extraction
functions = extract_called_functions(label)

print("All extracted calls:")
print(functions)

# Optional: filter only ai_* functions
ai_functions = [f for f in functions if f.startswith("ai_")]

print("\nFiltered ai_* calls:")
print(ai_functions)