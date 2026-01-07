#!/usr/bin/env npx tsx
/**
 * Interactive plugin installer for UnrealMCP
 * Finds Unreal projects and allows you to select one to install the plugin to
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { execSync } from 'child_process';

const PLATFORM = os.platform();
const IS_WINDOWS = PLATFORM === 'win32';

interface UnrealProject {
    name: string;
    path: string;
    uprojectPath: string;
}

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

function findUProjectFiles(searchPaths: string[]): UnrealProject[] {
    const projects: UnrealProject[] = [];
    
    for (const searchPath of searchPaths) {
        if (!fs.existsSync(searchPath)) {
            continue;
        }
        
        try {
            const files = fs.readdirSync(searchPath, { recursive: true, withFileTypes: true });
            
            for (const file of files) {
                if (file.isFile() && file.name.endsWith('.uproject')) {
                    const fullPath = path.join(file.path || searchPath, file.name);
                    try {
                        const projectName = path.basename(file.name, '.uproject');
                        projects.push({
                            name: projectName,
                            path: path.dirname(fullPath),
                            uprojectPath: fullPath,
                        });
                    } catch (e) {
                        // Skip invalid projects
                    }
                }
            }
        } catch (e) {
            // Skip directories we can't read
        }
    }
    
    return projects;
}

function getCommonProjectPaths(): string[] {
    const paths: string[] = [];
    
    if (IS_WINDOWS) {
        // Windows common locations
        const documents = path.join(os.homedir(), 'Documents');
        paths.push(
            path.join(documents, 'Unreal Projects'),
            path.join(os.homedir(), 'OneDrive', 'Documents', 'Unreal Projects'),
            'C:\\Users\\Public\\Documents\\Unreal Projects',
        );
    } else if (PLATFORM === 'darwin') {
        // Mac common locations
        paths.push(
            path.join(os.homedir(), 'Documents', 'Unreal Projects'),
            path.join(os.homedir(), 'Desktop'),
        );
    } else {
        // Linux common locations
        paths.push(
            path.join(os.homedir(), 'Documents', 'Unreal Projects'),
            path.join(os.homedir(), 'UnrealProjects'),
            path.join(os.homedir(), 'Desktop'),
        );
    }
    
    // Also check current directory and parent
    paths.push(process.cwd());
    paths.push(path.resolve(process.cwd(), '..'));
    
    return paths.filter(p => fs.existsSync(p));
}

function readUProjectFile(uprojectPath: string): any {
    try {
        const content = fs.readFileSync(uprojectPath, 'utf-8');
        // Remove BOM if present
        const cleanContent = content.replace(/^\uFEFF/, '');
        return JSON.parse(cleanContent);
    } catch (e) {
        return null;
    }
}

function writeUProjectFile(uprojectPath: string, data: any): void {
    const content = JSON.stringify(data, null, '\t');
    fs.writeFileSync(uprojectPath, content, 'utf-8');
}

function isPluginEnabled(uprojectData: any, pluginName: string): boolean {
    if (!uprojectData.Plugins) {
        return false;
    }
    
    return uprojectData.Plugins.some((p: any) => p.Name === pluginName);
}

function enablePluginInUProject(uprojectPath: string, pluginName: string): void {
    const data = readUProjectFile(uprojectPath);
    if (!data) {
        log(`  Warning: Could not read .uproject file`, 'yellow');
        return;
    }
    
    if (!data.Plugins) {
        data.Plugins = [];
    }
    
    if (!isPluginEnabled(data, pluginName)) {
        data.Plugins.push({
            Name: pluginName,
            Enabled: true,
        });
        writeUProjectFile(uprojectPath, data);
        log(`  Plugin enabled in .uproject file`, 'green');
    } else {
        log(`  Plugin already enabled in .uproject file`, 'green');
    }
}

async function promptSelection<T>(items: T[], displayFn: (item: T, index: number) => string): Promise<T | null> {
    return new Promise((resolve) => {
        const readline = require('readline');
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
        });
        
        // Display options
        items.forEach((item, index) => {
            log(`  ${index + 1}. ${displayFn(item, index)}`, 'white');
        });
        log(`  ${items.length + 1}. Cancel`, 'white');
        log('');
        
        rl.question('Select a project (number): ', (answer: string) => {
            rl.close();
            const index = parseInt(answer, 10) - 1;
            
            if (index >= 0 && index < items.length) {
                resolve(items[index]);
            } else {
                resolve(null);
            }
        });
    });
}

async function main(): Promise<void> {
    log('\nUnrealMCP Plugin Installer', 'cyan');
    log('==========================\n', 'cyan');
    
    const scriptDir = __dirname;
    const pluginSourcePath = path.resolve(scriptDir, '..', 'MCPGameProject', 'Plugins', 'UnrealMCP');
    
    // Verify plugin exists
    if (!fs.existsSync(pluginSourcePath)) {
        log(`ERROR: Plugin not found at: ${pluginSourcePath}`, 'red');
        log('Please build the plugin first using: npm run build-plugin', 'yellow');
        process.exit(1);
    }
    
    log(`Plugin source: ${pluginSourcePath}`, 'white');
    log('');
    
    // Find Unreal projects
    log('Searching for Unreal projects...', 'cyan');
    const searchPaths = getCommonProjectPaths();
    log(`  Searching in ${searchPaths.length} location(s)...`, 'white');
    
    const projects = findUProjectFiles(searchPaths);
    
    if (projects.length === 0) {
        log('\nNo Unreal projects found in common locations.', 'yellow');
        log('\nYou can manually install the plugin by:', 'yellow');
        log('  1. Copy the plugin folder to your project:', 'white');
        log(`     ${pluginSourcePath}`, 'white');
        log('     → YourProject/Plugins/UnrealMCP', 'white');
        log('  2. Enable the plugin in your .uproject file or via Editor > Plugins', 'white');
        process.exit(0);
    }
    
    log(`  Found ${projects.length} project(s)\n`, 'green');
    
    // Show projects and let user select
    log('Available projects:', 'cyan');
    const selectedProject = await promptSelection(
        projects,
        (project) => `${project.name} (${project.path})`
    );
    
    if (!selectedProject) {
        log('\nInstallation cancelled.', 'yellow');
        process.exit(0);
    }
    
    log('');
    log(`Selected: ${selectedProject.name}`, 'green');
    log(`  Path: ${selectedProject.path}`, 'white');
    log(`  .uproject: ${selectedProject.uprojectPath}`, 'white');
    log('');
    
    // Check if plugins directory exists
    const pluginsDir = path.join(selectedProject.path, 'Plugins');
    if (!fs.existsSync(pluginsDir)) {
        log('Creating Plugins directory...', 'cyan');
        fs.mkdirSync(pluginsDir, { recursive: true });
        log('  Plugins directory created', 'green');
    }
    
    // Check if plugin already exists
    const pluginDestPath = path.join(pluginsDir, 'UnrealMCP');
    if (fs.existsSync(pluginDestPath)) {
        log('Plugin already exists at destination.', 'yellow');
        const readline = require('readline');
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
        });
        
        const answer = await new Promise<string>((resolve) => {
            rl.question('Overwrite? (y/N): ', resolve);
        });
        rl.close();
        
        if (answer.toLowerCase() !== 'y') {
            log('Installation cancelled.', 'yellow');
            process.exit(0);
        }
        
        log('Removing existing plugin...', 'cyan');
        fs.rmSync(pluginDestPath, { recursive: true, force: true });
    }
    
    // Copy plugin
    log('Copying plugin...', 'cyan');
    try {
        // Use platform-specific copy command for better reliability
        if (IS_WINDOWS) {
            execSync(`xcopy /E /I /Y "${pluginSourcePath}" "${pluginDestPath}"`, { stdio: 'inherit' });
        } else {
            execSync(`cp -r "${pluginSourcePath}" "${pluginDestPath}"`, { stdio: 'inherit' });
        }
        log('  Plugin copied successfully', 'green');
    } catch (e) {
        log(`  ERROR: Failed to copy plugin: ${e}`, 'red');
        process.exit(1);
    }
    
    // Enable plugin in .uproject file
    log('Enabling plugin in .uproject file...', 'cyan');
    enablePluginInUProject(selectedProject.uprojectPath, 'UnrealMCP');
    
    log('');
    log('==========================', 'green');
    log('Installation completed!', 'green');
    log('==========================', 'green');
    log('');
    log('Next steps:', 'cyan');
    log('  1. Open your project in Unreal Editor', 'white');
    log('  2. The plugin should be enabled automatically', 'white');
    log('  3. If prompted, restart the editor', 'white');
    log('');
    log(`Plugin installed to: ${pluginDestPath}`, 'white');
}

main().catch((err) => {
    const error = err as Error;
    log(`\nFatal error: ${error.message}`, 'red');
    if (error.stack) {
        log(error.stack, 'red');
    }
    process.exit(1);
});

