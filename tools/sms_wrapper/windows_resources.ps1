# Native provider for host_bootstrap.py resources. WSL is never started.
param([switch]$Processes)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$errorsBySource = @{}
function Read-Source($name, [scriptblock]$query) {
    try { & $query } catch { $errorsBySource[$name] = $_.Exception.Message }
}
$cpu = Read-Source cpu { Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'" }
$mem = Read-Source memory { Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory }
$os = Read-Source os { Get-CimInstance Win32_OperatingSystem }
$disk = Read-Source disk { Get-CimInstance Win32_PerfFormattedData_PerfDisk_PhysicalDisk -Filter "Name='_Total'" }
$zones = @(Read-Source thermal {
    Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature | ForEach-Object {
        [ordered]@{
            name = $_.InstanceName
            source = 'MSAcpi_ThermalZoneTemperature'
            current_c = if ($_.CurrentTemperature -gt 0) { [math]::Round($_.CurrentTemperature / 10 - 273.15, 2) }
            passive_trip_c = if ($_.PassiveTripPoint -gt 0) { [math]::Round($_.PassiveTripPoint / 10 - 273.15, 2) }
        }
    }
})
if (-not @($zones | Where-Object { $null -ne $_.current_c }).Count) {
    $zones += @(Read-Source thermal_performance {
        Get-CimInstance Win32_PerfFormattedData_Counters_ThermalZoneInformation | ForEach-Object {
            [ordered]@{
                name = $_.Name
                source = 'Win32_PerfFormattedData_Counters_ThermalZoneInformation'
                current_c = if ($_.Temperature -gt 0) { [math]::Round($_.Temperature - 273.15, 2) }
                passive_trip_c = $null
                percent_passive_limit = $_.PercentPassiveLimit
            }
        }
    })
    if ($os.LastBootUpTime -and $zones.Count) {
        # Kernel-Power 125 records enumerated zone trip points in Kelvin.
        $events = @(Read-Source thermal_limits {
            Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-Kernel-Power';
                Id=125; StartTime=$os.LastBootUpTime} -MaxEvents 32
        })
        $limits = @{}
        foreach ($event in $events) {
            $fields = @{}
            foreach ($field in ([xml]$event.ToXml()).Event.EventData.Data) {
                $fields[$field.Name] = $field.'#text'
            }
            $zoneName = $fields['ThermalZoneDeviceInstance']
            if ($zoneName -and -not $limits.ContainsKey($zoneName)) { $limits[$zoneName] = $fields }
        }
        foreach ($zone in $zones) {
            if ($limits.ContainsKey($zone.name) -and [int]$limits[$zone.name]['_PSV'] -gt 0) {
                $zone.passive_trip_c = [math]::Round([int]$limits[$zone.name]['_PSV'] - 273.15, 2)
                $zone.trip_source = 'Kernel-Power/125'
            }
        }
    }
}
$sample = [ordered]@{
    cpu_percent = $cpu.PercentProcessorTime
    total_bytes = if ($os) { [long]$os.TotalVisibleMemorySize * 1024 }
    available_bytes = $mem.AvailableBytes
    pages_input_per_sec = $mem.PagesInputPersec
    pages_output_per_sec = $mem.PagesOutputPersec
    disk_queue = $disk.CurrentDiskQueueLength
    disk_bytes_per_sec = $disk.DiskBytesPersec
    thermal_zones = $zones
    errors = $errorsBySource
}
if ($Processes) {
    $sample.processes = @(Read-Source processes {
        Get-CimInstance Win32_Process | Sort-Object WorkingSetSize -Descending | ForEach-Object {
            [ordered]@{ pid = $_.ProcessId; rss_bytes = $_.WorkingSetSize; name = $_.Name; command = $_.CommandLine }
        }
    })
}
$sample | ConvertTo-Json -Depth 5 -Compress
