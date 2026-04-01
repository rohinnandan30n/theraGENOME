# SPAdes WSL Installation - Complete Summary

**Installation Date:** March 30, 2026  
**Status:** ✅ COMPLETE AND VERIFIED

## Installation Components

### ✅ FastQC (Already Installed)
- **Location:** `C:\Stuff\fastqc\FastQC`
- **Version:** v0.12.1
- **Status:** WORKING
- **Verification:** `fastqc --version` → FastQC v0.12.1

### ✅ SPAdes via WSL (Now Installed)
- **Linux Path (in WSL):** `/usr/bin/spades.py`
- **Windows Wrapper:** `C:\Stuff\spades\bin\spades.py`
- **Windows Wrapper Detection:** WSL-first strategy
- **Version:** SPAdes genome assembler v3.15.5
- **Installation Method:** `wsl sudo apt install spades`
- **Status:** WORKING
- **Verification:** `wsl spades.py --version` → SPAdes genome assembler v3.15.5

### ✅ API Integration
- **File:** `src/api/pathogens.py`
- **Function:** `run_spades(r1_path, r2_path, output_dir)`
- **Command Format:** `spades.py -1 <r1_path> -2 <r2_path> -o <output_dir>`
- **Wrapper Behavior:** Automatically detects WSL and delegates
- **Status:** READY

## How It Works

1. **User uploads genomic files** via API endpoint
2. **FastQC validation** runs on both read pairs
3. **SPAdes assembly** starts automatically if FastQC passes
4. **Wrapper script** (`C:\Stuff\spades\bin\spades.py`) intercepts `spades.py` command
5. **WSL detection** - Wrapper finds WSL and delegates
6. **WSL execution** - `wsl spades.py` runs in Linux environment
7. **Results** - Assembly files saved to `uploads/{job_id}/assembly/`

## API Setup and Usage

### Quick Start

```bash
# Navigate to API directory
cd C:\Stuff\VSC\Repos\cmrit\services\dev2-pathogen-resistance-api

# Install Python dependencies
pip install -r requirements.txt

# Start the API
python main.py

# Open browser to http://localhost:8000/docs
```

### Testing the Installation

**Verify FastQC:**
```bash
fastqc --version
# Expected: FastQC v0.12.1
```

**Verify SPAdes:**
```bash
spades.py --version
# Expected: SPAdes genome assembler v3.15.5

# Or via WSL directly:
wsl spades.py --version
```

**Test full integration:**
```bash
# Use the included test script
python test_spades_integration.py
```

## Technical Details

### Wrapper Script Location
- File: `C:\Stuff\spades\bin\spades.py`
- Type: Windows batch script (.bat renamed to .py)
- Function: Intelligent proxy that detects WSL and delegates

### Path Handling
- Windows paths like `C:\data\reads.fastq` work directly in WSL
- WSL automatically converts Windows paths to Linux paths
- No manual path conversion needed

### Error Handling
The wrapper will:
1. Try WSL first (if installed) ✓ AVAILABLE
2. Try Docker second (if installed) ○ OPTIONAL
3. Try Conda third ○ OPTIONAL
4. Show clear error and instructions if none available

## File Locations

```
C:\Stuff\
├── fastqc/
│   └── FastQC/
│       ├── fastqc.bat
│       └── [FastQC binaries]
└── spades/
    └── bin/
        └── spades.py (wrapper)

C:\Stuff\VSC\Repos\cmrit\services\dev2-pathogen-resistance-api/
├── src/
│   └── api/
│       └── pathogens.py (uses run_spades function)
├── uploads/ (assembly results stored here)
├── README.md (updated with setup info)
├── WINDOWS_SETUP.md (comprehensive setup guide)
├── test_spades_integration.py (integration test)
└── requirements.txt

WSL Ubuntu:
/usr/bin/spades.py (actual SPAdes executable)
```

## Verification Checklist

- ✅ FastQC v0.12.1 installed and working
- ✅ WSL with Ubuntu installed
- ✅ SPAdes v3.15.5 installed in WSL at `/usr/bin/spades.py`
- ✅ Windows wrapper script created at `C:\Stuff\spades\bin\spades.py`
- ✅ SPAdes bin directory added to user PATH
- ✅ API `run_spades()` function ready to call SPAdes
- ✅ Wrapper detects WSL and delegates correctly
- ✅ File paths handled automatically

## What's Next

1. **Ensure Python is installed** on your system
2. **Install API dependencies:** `pip install -r requirements.txt`
3. **Start the API:** `python main.py`
4. **Test with sample genomic data:**
   - Upload FASTQ files via API
   - FastQC validation will run
   - SPAdes assembly will begin automatically
   - Results saved to `uploads/{job_id}/assembly/`

## Troubleshooting

### SPAdes not found?
```bash
# Verify WSL installation
wsl which spades.py
# Should show: /usr/bin/spades.py

# If not found, install:
wsl sudo apt update
wsl sudo apt install spades -y
```

### Wrapper not working?
```bash
# Test wrapper directly
C:\Stuff\spades\bin\spades.py --version

# Or test WSL directly
wsl spades.py --version
```

### Path issues?
```bash
# Verify PATH contains SPAdes wrapper directory
$env:Path -split ';' | Select-String 'spades'
# Should find: C:\Stuff\spades\bin

# Reload PATH from environment
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
$machinePath = [Environment]::GetEnvironmentVariable('Path','Machine')
$env:Path = "$userPath;$machinePath"
```

## Support

For issues with:
- **FastQC:** https://www.bioinformatics.babraham.ac.uk/projects/fastqc/
- **SPAdes:** http://spades.bioinf.spbau.ru/
- **WSL:** https://docs.microsoft.com/windows/wsl/

## Documentation

- **API Documentation:** http://localhost:8000/docs (when running)
- **Setup Guide:** [WINDOWS_SETUP.md](WINDOWS_SETUP.md)
- **README:** [README.md](README.md)
- **Test Script:** [test_spades_integration.py](test_spades_integration.py)
