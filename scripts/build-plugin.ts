#!/usr/bin/env npx tsx
/**
 * Build script for UnrealMCP plugin
 * Cross-platform build script for Windows, Mac, and Linux
 */

import { execSync, spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import * as readline from 'readline';

// Configuration
const PLATFORM = os.platform();
const IS_WINDOWS = PLATFORM === 'win32';
const IS_MAC = PLATFORM === 'darwin';
const IS_LINUX = PLATFORM === 'linux';

// Get project path (relative to script location)
const scriptDir = __dirname;
const projectPath = path.resolve(scriptDir, '..', 'MCPGameProject', 'MCPGameProject.uproject');

interface EngineInfo {
    enginePath: string;
    ubtPath: string;
}

// Unreal Engine installation paths by platform
const UNREAL_PATHS: Record<string, string[]> = {
    win32: [
        'C:\\Program Files\\Epic Games\\UE_5.7',
        'C:\\Program Files\\Epic Games\\UE_5.6',
        'C:\\Program Files\\Epic Games\\UE_5.5',
        'C:\\Program Files\\Epic Games\\UE_5.4',
        'C:\\Program Files\\Epic Games\\UE_5.3',
    ],
    darwin: [
        '/Users/Shared/Epic Games/UE_5.7',
        '/Users/Shared/Epic Games/UE_5.6',
        '/Users/Shared/Epic Games/UE_5.5',
        '/Users/Shared/Epic Games/UE_5.4',
        '/Users/Shared/Epic Games/UE_5.3',
        // Also check user's Applications folder
        path.join(os.homedir(), 'Library', 'UnrealEngine', 'UE_5.7'),
        path.join(os.homedir(), 'Library', 'UnrealEngine', 'UE_5.6'),
        path.join(os.homedir(), 'Library', 'UnrealEngine', 'UE_5.5'),
    ],
    linux: [
        path.join(os.homedir(), 'UnrealEngine', 'UE_5.7'),
        path.join(os.homedir(), 'UnrealEngine', 'UE_5.6'),
        path.join(os.homedir(), 'UnrealEngine', 'UE_5.5'),
        path.join(os.homedir(), 'UnrealEngine', 'UE_5.4'),
        path.join(os.homedir(), 'UnrealEngine', 'UE_5.3'),
        '/opt/unreal-engine/UE_5.7',
        '/opt/unreal-engine/UE_5.6',
        '/opt/unreal-engine/UE_5.5',
    ],
};

// UnrealBuildTool executable paths by platform
const UBT_PATHS: Record<string, (enginePath: string) => string> = {
    win32: (enginePath: string) => path.join(enginePath, 'Engine', 'Binaries', 'DotNET', 'UnrealBuildTool', 'UnrealBuildTool.exe'),
    darwin: (enginePath: string) => path.join(enginePath, 'Engine', 'Build', 'BatchFiles', 'Mac', 'Build.sh'),
    linux: (enginePath: string) => path.join(enginePath, 'Engine', 'Build', 'BatchFiles', 'Linux', 'Build.sh'),
};

// Colors for terminal output
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    cyan: '\x1b[36m',
    white: '\x1b[37m',
};

function log(message: string, color: keyof typeof colors = 'white'): void {
    const colorCode = colors[color] || colors.white;
    console.log(`${colorCode}${message}${colors.reset}`);
}

function findUnrealEngine(): EngineInfo | null {
    const paths = UNREAL_PATHS[PLATFORM] || [];
    
    for (const enginePath of paths) {
        const ubtPath = UBT_PATHS[PLATFORM](enginePath);
        if (fs.existsSync(ubtPath)) {
            return { enginePath, ubtPath };
        }
    }
    
    return null;
}

function checkEditorRunning(): boolean {
    try {
        if (IS_WINDOWS) {
            const result = execSync('tasklist /FI "IMAGENAME eq UnrealEditor*.exe"', { encoding: 'utf-8', stdio: 'pipe' });
            return result.includes('UnrealEditor');
        } else if (IS_MAC || IS_LINUX) {
            const result = execSync('pgrep -f "UnrealEditor"', { encoding: 'utf-8', stdio: 'pipe' });
            return result.trim().length > 0;
        }
    } catch (e) {
        // Command failed, assume editor is not running
        return false;
    }
    return false;
}

function execCommand(command: string, args: string[], options: { shell?: boolean } = {}): Promise<number> {
    return new Promise((resolve, reject) => {
        const proc = spawn(command, args, {
            stdio: 'inherit',
            shell: IS_WINDOWS || options.shell,
            ...options,
        });
        
        proc.on('close', (code) => {
            if (code === 0) {
                resolve(code);
            } else {
                reject(new Error(`Command failed with exit code ${code}`));
            }
        });
        
        proc.on('error', (err) => {
            reject(err);
        });
    });
}

function promptUser(question: string): Promise<string> {
    return new Promise((resolve) => {
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
        });
        
        rl.question(question, (answer) => {
            rl.close();
            resolve(answer);
        });
    });
}

async function main(): Promise<void> {
    log('\nUnrealMCP Plugin Build Script', 'cyan');
    log('=============================\n', 'cyan');
    
    // Verify project file exists
    if (!fs.existsSync(projectPath)) {
        log(`ERROR: Project file not found: ${projectPath}`, 'red');
        process.exit(1);
    }
    
    log(`Project: ${projectPath}`, 'white');
    
    // Find Unreal Engine
    const engine = findUnrealEngine();
    if (!engine) {
        log('\nERROR: Could not find Unreal Engine installation', 'red');
        log('Please ensure Unreal Engine is installed in one of these locations:', 'yellow');
        (UNREAL_PATHS[PLATFORM] || []).forEach(p => log(`  - ${p}`, 'yellow'));
        process.exit(1);
    }
    
    log(`Unreal Engine: ${engine.enginePath}`, 'white');
    log(`UnrealBuildTool: ${engine.ubtPath}\n`, 'white');
    
    // Check if editor is running
    if (checkEditorRunning()) {
        log('WARNING: Unreal Editor appears to be running!', 'yellow');
        log('  Live Coding must be disabled for the build to succeed.', 'yellow');
        log('\nOptions:', 'yellow');
        log('  1. Close Unreal Editor completely', 'yellow');
        log('  2. In Unreal Editor, press Ctrl+Alt+F11 (Cmd+Alt+F11 on Mac) to disable Live Coding', 'yellow');
        log('');
        
        // On non-Windows, we can't easily prompt, so just warn
        if (IS_WINDOWS) {
            const answer = await promptUser('Continue anyway? (y/N): ');
            if (answer.toLowerCase() !== 'y') {
                log('Build cancelled.', 'yellow');
                process.exit(1);
            }
        } else {
            log('Continuing with build... (editor may need to be closed)', 'yellow');
        }
    }
    
    // Step 1: Regenerate project files
    log('\nStep 1: Regenerating project files...', 'cyan');
    try {
        if (IS_WINDOWS) {
            await execCommand(engine.ubtPath, [
                '-projectfiles',
                `-project="${projectPath}"`,
                '-game',
                '-rocket',
                '-progress',
            ]);
        } else {
            // On Mac/Linux, use the Build.sh script
            await execCommand('bash', [
                engine.ubtPath,
                '-projectfiles',
                `-project="${projectPath}"`,
                '-game',
                '-rocket',
                '-progress',
            ]);
        }
        log('  Project files regenerated successfully', 'green');
    } catch (err) {
        const error = err as Error;
        log(`  Warning: Project file regeneration had issues: ${error.message}`, 'yellow');
        log('  Continuing with build anyway...', 'yellow');
    }
    
    // Step 2: Build the plugin
    log('\nStep 2: Building plugin...', 'cyan');
    log('  Target: MCPGameProjectEditor', 'white');
    const buildPlatform = IS_WINDOWS ? 'Win64' : (IS_MAC ? 'Mac' : 'Linux');
    log(`  Platform: ${buildPlatform}`, 'white');
    log('  Configuration: Development', 'white');
    log('');
    
    try {
        if (IS_WINDOWS) {
            await execCommand(engine.ubtPath, [
                'MCPGameProjectEditor',
                'Win64',
                'Development',
                `-project="${projectPath}"`,
                '-rocket',
                '-progress',
            ]);
        } else {
            // On Mac/Linux, build for the appropriate platform
            await execCommand('bash', [
                engine.ubtPath,
                'MCPGameProjectEditor',
                buildPlatform,
                'Development',
                `-project="${projectPath}"`,
                '-rocket',
                '-progress',
            ]);
        }
        
        log('\n=============================', 'green');
        log('Build completed successfully!', 'green');
        log('=============================\n', 'green');
        
        // Show plugin binary location
        const binaryName = IS_WINDOWS ? 'UnrealEditor-UnrealMCP.dll' : 
                          IS_MAC ? 'UnrealEditor-UnrealMCP.dylib' : 
                          'UnrealEditor-UnrealMCP.so';
        const pluginBinaryPath = path.resolve(
            scriptDir, '..', 'MCPGameProject', 'Plugins', 'UnrealMCP', 
            'Binaries', buildPlatform, binaryName
        );
        
        log('Plugin binary location:', 'white');
        if (fs.existsSync(pluginBinaryPath)) {
            log(`  ${pluginBinaryPath}`, 'green');
        } else {
            log('  (Binary not found at expected location)', 'yellow');
        }
        
        process.exit(0);
    } catch (err) {
        const error = err as Error;
        log('\n=============================', 'red');
        log(`Build failed: ${error.message}`, 'red');
        log('=============================\n', 'red');
        
        log('Common issues:', 'yellow');
        log('  - Unreal Editor is running with Live Coding enabled', 'yellow');
        log('  - Missing dependencies or incorrect Unreal Engine version', 'yellow');
        log('  - Compilation errors in C++ code', 'yellow');
        
        process.exit(1);
    }
}

// Run the script
main().catch((err) => {
    const error = err as Error;
    log(`\nFatal error: ${error.message}`, 'red');
    process.exit(1);
});

