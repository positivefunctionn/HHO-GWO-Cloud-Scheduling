@echo off
setlocal
cd /d "%~dp0"
echo ======================================================
echo HHO-GWO full synthetic reproduction
 echo This runs 2,520 benchmark rows across two profiles.
echo It can take several minutes. Do not close this window.
echo ======================================================
py -m pip install -r requirements.txt
if errorlevel 1 goto fail
py -m unittest discover -s tests -v
if errorlevel 1 goto fail
py experiments\run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 10 --seed-start 9601 --task-counts 20,50,100 --load-levels low,moderate,high --evaluation-budget 300 --power-curve-exponent 2.0 --objective-profile balanced --hybrid-hho-fraction 0.05 --hybrid-gwo-fraction 0.05 --algorithms "ACO,WOA,ABC,GWO,GA,HHO,HHO-GWO" --output results\reproduction_balanced_9601
if errorlevel 1 goto fail
py experiments\run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 10 --seed-start 9701 --task-counts 20,50,100 --load-levels low,moderate,high --evaluation-budget 300 --power-curve-exponent 2.0 --objective-profile balanced --hybrid-hho-fraction 0.05 --hybrid-gwo-fraction 0.05 --algorithms "ACO,WOA,ABC,GWO,GA,HHO,HHO-GWO" --output results\reproduction_balanced_9701
if errorlevel 1 goto fail
py experiments\merge_benchmark_batches.py results\reproduction_balanced_9601 results\reproduction_balanced_9701 --output results\reproduction_balanced_merged
if errorlevel 1 goto fail
py experiments\analyze_synthetic_results.py results\reproduction_balanced_merged --reference HHO-GWO --metrics realized_fitness,realized_energy,realized_sla_rate,realized_makespan,load_imbalance --alternative two-sided
if errorlevel 1 goto fail
py experiments\run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 20 --seed-start 12001 --task-counts 20,50,100 --load-levels low,moderate,high --evaluation-budget 100 --power-curve-exponent 2.0 --objective-profile sla --hybrid-hho-fraction 0.05 --hybrid-gwo-fraction 0.45 --algorithms "HHO-GWO,GWO,HHO,GA,ACO,WOA,ABC" --output results\reproduction_sla
if errorlevel 1 goto fail
py experiments\analyze_synthetic_results.py results\reproduction_sla --reference HHO-GWO --metrics realized_sla_rate --alternative less
if errorlevel 1 goto fail
echo.
echo SUCCESS: both synthetic experiment profiles completed and analyzed.
echo Results are under results\reproduction_balanced_merged and results\reproduction_sla.
echo These are synthetic results, not CloudSim or production-cloud validation.
pause
exit /b 0
:fail
echo.
echo FAILED: read the error above. Share the complete terminal output before retrying.
pause
exit /b 1
