# SPAdes and FastQC Setup for Windows

This guide provides step-by-step instructions to set up FastQC and SPAdes on Windows for the Pathogen & Resistance API.

## Summary

- **FastQC:** Already installed at `C:\Stuff\fastqc\FastQC` and accessible globally as `fastqc`
- **SPAdes:** ✅ **INSTALLED in WSL** at `/usr/bin/spades.py` (v3.15.5)
  - Wrapper installed at `C:\Stuff\spades\bin\spades.py`
  - Can be called from Windows via wrapper: `spades.py`

## FastQC Status

✅ **FastQC is ready to use:**

```bash
fastqc --version
# Output: FastQC v0.12.1
```

FastQC is installed at:
```
C:\Stuff\fastqc\FastQC
```

And is added to your PATH for global access.

## SPAdes Status

✅ **SPAdes is NOW INSTALLED and READY TO USE!**

```bash
wsl spades.py --version
# Output: SPAdes genome assembler v3.15.5

spades.py --version
# Also works via Windows wrapper (delegates to WSL automatically)
```

### Installation Details:

- **Location in WSL:** `/usr/bin/spades.py`
- **Windows Wrapper:** `C:\Stuff\spades\bin\spades.py`
- **Version:** SPAdes genome assembler v3.15.5
- **Method:** Installed via WSL Ubuntu package manager

### How It Works:

The Windows wrapper script at `C:\Stuff\spades\bin\spades.py`:
1. Detects that WSL is installed
2. Automatically delegates the command to WSL
3. SPAdes runs in the Linux environment via WSL
4. Results are returned to Windows

You can call it the same way:
```bash
spades.py -1 reads_R1.fastq -2 reads_R2.fastq -o assembly/
```

The wrapper handles all the WSL integration automatically.

## Running the API

### Quick Start (SPAdes Already Installed):

```bash
# 1. Open any terminal (PowerShell, cmd, or Git Bash)
# 2. Navigate to the API directory
cd C:\Stuff\VSC\Repos\cmrit\services\dev2-pathogen-resistance-api

# 3. Install Python dependencies (first time only)
pip install -r requirements.txt

# 4. Start the API
python main.py

# 5. Open http://localhost:8000/docs in your browser
```

That's it! SPAdes is already installed in WSL and will be called automatically when you upload genomic data.

## Alternative Setups (Optional)

If you prefer to use Docker or Conda instead of WSL, follow these steps.

### Option A: Docker Desktop (Alternative)

If you prefer to use Docker instead of WSL:

1. **Download and install Docker Desktop:**
   - https://www.docker.com/products/docker-desktop
   
2. **Pull the SPAdes Docker image:**
   ```bash
   docker pull quay.io/biocontainers/spades:4.3.0--cpu
   ```
   
3. **The wrapper will automatically detect Docker** and use it if WSL is not available

### Option B: Conda (Alternative)

If you prefer Conda environment management:

1. **Install Miniconda:**
   - https://docs.conda.io/en/latest/miniconda.html

2. **Open Conda Prompt and install:**
   ```bash
   conda install -c bioconda spades
   ```

3. **Always run the API from the Conda Prompt** with the bioconda packages available

## Testing the Installation

### Verify FastQC:
```bash
fastqc --version
# Expected: FastQC v0.12.1
```

### Verify SPAdes:
```bash
spades.py --version
# Expected: SPAdes genome assembler v3.15.5
```

## Troubleshooting

### "SPAdes is not installed or not found"

**First, verify SPAdes IS installed:**

```bash
# Direct WSL check
wsl spades.py --version
# Should show: SPAdes genome assembler v3.15.5

# Via wrapper
spades.py --version
# Should work (wrapper detects WSL and delegates)
```

If SPAdes is not found in WSL, install it:
```bash
# Open WSL terminal
wsl

# Install SPAdes
sudo apt update
sudo apt install spades -y

# Verify
spades.py --version
```

### "FastQC command not found"

FastQC should be at `C:\Stuff\fastqc\FastQC`. Verify PATH:
```bash
where.exe fastqc
# Should show path to fastqc
```

If not found, add to PATH manually or reinstall FastQC.

### API returns assembly errors

**Check logs for specific SPAdes errors:**
1. Look at API console output for error messages
2. Check that input FASTQ files are valid
3. Verify FastQC passed (should be since API checks this)
4. Try assembly manually: `spades.py -1 test_R1.fastq -2 test_R2.fastq -o assembly_test/`

### WSL not detecting SPAdes

If WSL is installed but `wsl spades.py` doesn't work:

```bash
# Check SPAdes installation in WSL
wsl which spades.py
# Should show: /usr/bin/spades.py

# If not found, install it
wsl sudo apt update
wsl sudo apt install spades -y
```

### "Permission denied" errors

For Linux-style permission errors in WSL:
```bash
wsl sudo chmod +x /usr/bin/spades.py
```

### Multiple Python versions conflict

If you have both system Python and Conda Python:
- Make sure to use the same Python throughout
- Or activate Conda environment: `conda activate base`
- Verify Python path: `where python`

## File Locations

```
C:\Stuff\fastqc\               # FastQC directory
├── FastQC/
│   └── fastqc.bat            # FastQC launcher

C:\Stuff\spades/              # SPAdes wrapper directory
├── bin/
│   └── spades.py             # SPAdes wrapper script

C:\Stuff\VSC\Repos\cmrit\     # Project directory
├── services/
│   └── dev2-pathogen-resistance-api/
│       ├── src/
│       ├── uploads/          # Generated genome data
│       ├── main.py
│       └── requirements.txt
```

## Next Steps

1. **Choose one option** (Docker, WSL, or Conda) from above
2. **Follow the installation steps** for that option
3. **Verify installations:**
   ```bash
   fastqc --version
   spades.py --version
   ```
4. **Start the API:**
   ```bash
   cd C:\Stuff\VSC\Repos\cmrit\services\dev2-pathogen-resistance-api
   python main.py
   ```
5. **Access the API:** http://localhost:8000/docs

## Support

For issues with:
- **FastQC:** https://www.bioinformatics.babraham.ac.uk/projects/fastqc/
- **SPAdes:** http://spades.bioinf.spbau.ru/
- **Docker:** https://docs.docker.com/
- **WSL:** https://docs.microsoft.com/en-us/windows/wsl/
- **Conda:** https://docs.conda.io/
