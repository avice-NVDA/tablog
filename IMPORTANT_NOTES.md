# Important Notes for TabLog Development

## ⚠️ CRITICAL: Storage Location Best Practices

### What Happened (Learning from v1.2.0 Development)

During the development of v1.2.0, we tested two solutions to fix the GLIBCXX incompatibility:

1. **Solution A:** Virtual environment in tablog directory (scratch storage) ✅
2. **Solution B:** Conda environment in user's home directory ❌

### The Problem with Home Directory Storage

**Solution B installed Miniconda to `/home/avice/miniconda3_tablog/`**
- Size: 2.1 GB
- Result: **Home directory filled to 100%!** ❌
- Impact: User couldn't work until it was removed

### The Lesson

**NEVER install large dependencies in home directories!**

Home directories typically have strict quotas (often 5 GB or less). Instead:

#### ✅ DO:
- Install to **scratch storage** (`/home/scratch.${USER}_vlsi/`)
- Install to **shared project directories**
- Install to **dedicated storage partitions**

#### ❌ DON'T:
- Install to `~/` (home directory)
- Install to `/home/${USER}/`
- Install large packages without checking `df -h /home/${USER}`

### Why Solution A Was Chosen

1. ✅ **Location:** In project directory (scratch storage)
2. ✅ **Size:** Only 227 MB (vs 2.1 GB for conda)
3. ✅ **Portability:** Copy entire folder, works immediately
4. ✅ **No home directory impact:** Safe for all users

---

## Storage Recommendations

### Before Installing Large Dependencies

Always check available space:
```bash
# Check home directory space
df -h /home/${USER}

# Check scratch storage space  
df -h /home/scratch.${USER}_vlsi
```

### Size Guidelines

| Size | Where to Install |
|------|------------------|
| < 100 MB | Home or scratch (either is fine) |
| 100 MB - 500 MB | Scratch preferred |
| 500 MB - 5 GB | Scratch only |
| > 5 GB | Dedicated storage partition |

### TabLog Sizes

- **Core application:** ~10 MB
- **Virtual environment:** ~227 MB
- **Total:** ~237 MB ✅ (reasonable for scratch)

---

## Virtual Environment Management

### Location
```
/home/scratch.avice_vlsi/tablog/venv_pyqt5_rebuild/
```

### Why Not in Git?

The virtual environment is **excluded from git** (in `.gitignore`) because:
1. Size: 227 MB is too large for git
2. Platform-specific: Binary files may not work on other systems
3. Easy to recreate: Use `setup_venv.sh` to rebuild

### For New Users

**Option 1: Copy from existing installation (fastest)**
```bash
# Copy entire tablog directory from another user
cp -r /home/scratch.avice_vlsi/tablog /home/scratch.YOUR_USER_vlsi/
cd /home/scratch.YOUR_USER_vlsi/tablog
./tablog example.log  # Works immediately!
```

**Option 2: Clone from GitHub and setup (slower)**
```bash
git clone github.com:avice-NVDA/tablog.git
cd tablog
./setup_venv.sh  # Creates venv (~5 minutes)
./tablog example.log
```

---

## Conda/Miniconda Guidelines

If you must use conda:

### ✅ DO:
```bash
# Install to scratch storage
cd /home/scratch.${USER}_vlsi/
mkdir -p conda_envs
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p /home/scratch.${USER}_vlsi/conda_envs/miniconda3
```

### ❌ DON'T:
```bash
# This will fill your home directory!
bash Miniconda3-latest-Linux-x86_64.sh  # Default: ~/miniconda3
```

---

## Monitoring Storage

### Regular Checks
```bash
# Check home directory usage
du -sh /home/${USER}
df -h /home/${USER}

# Check scratch directory usage
du -sh /home/scratch.${USER}_vlsi
df -h /home/scratch.${USER}_vlsi

# Find largest directories in home
du -h /home/${USER} | sort -rh | head -20
```

### Warning Signs
- Home directory > 80% full: ⚠️ Warning
- Home directory > 95% full: 🚨 Critical - remove files immediately!
- Getting "Disk quota exceeded" errors: 💥 Emergency - home is full!

---

## Summary

1. **Always use scratch storage** for large dependencies (> 100 MB)
2. **Check available space** before installing anything large
3. **Never use default conda installation** (goes to home)
4. **TabLog v1.2.0 follows best practices** - venv in project directory (scratch)
5. **Monitor your storage** regularly with `df -h`

---

**Remember:** Home directories are for small config files and personal settings, not large software installations!

---

_Last updated: December 4, 2025 (v1.2.0)_

