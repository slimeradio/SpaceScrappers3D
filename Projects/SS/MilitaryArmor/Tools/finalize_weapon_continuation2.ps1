$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
function Save-Crlf($path,$data){
 $text=if($data -is [string]){$data}else{$data|ConvertTo-Json -Depth 15}
 [IO.File]::WriteAllText($path,($text -replace "`r?`n","`r`n").TrimEnd()+"`r`n",[Text.UTF8Encoding]::new($false))
}
$catalog=Import-Csv (Join-Path $root '../Catalog/blocks.csv')
$baseline=Get-Content -Raw (Join-Path $root 'Tools/weapon-continuation2-source-baseline.json')|ConvertFrom-Json
foreach($entry in $baseline){if((Get-FileHash -LiteralPath $entry.path).Hash -ne $entry.hash){throw "Old source modified $($entry.path)"}}
$models=@();$previewCount=0
foreach($id in @('MA-W10','MA-W11','MA-W12')){
 $folder=Join-Path $root "Blocks/$id"
 $a=Get-Content -Raw (Join-Path $folder assembly.json)|ConvertFrom-Json
 $v=Get-Content -Raw (Join-Path $folder validation.json)|ConvertFrom-Json
 if(-not $v.checks_passed){throw "Validation failed $id"}
 $row=@($catalog|Where-Object ID -eq $a.catalog_id)
 if($row.Count -ne 1){throw "Catalog unresolved $id"}
 if($a.catalog_grid[0] -ne [int]$row[0].Ширина_клеток -or $a.catalog_grid[1] -ne [int]$row[0].Высота_клеток){throw "Grid mismatch $id"}
 foreach($i in $a.instances){
  $part=Join-Path $root "Parts/$($i.part_id)"
  $pm=Get-Content -Raw (Join-Path $part part.json)|ConvertFrom-Json
  if($pm.version -ne $i.version -or -not (Test-Path (Join-Path $folder $i.source))){throw "Part mismatch $id"}
 }
 $previews=@(Get-ChildItem (Join-Path $folder Previews) -Filter '*.png'|ForEach-Object {"Blocks/$id/Previews/$($_.Name)"})
 if($previews.Count -ne 3){throw "Preview count $id"}
 foreach($preview in $previews){
  $b=[IO.File]::ReadAllBytes((Join-Path $root $preview))
  if([Text.Encoding]::ASCII.GetString($b,1,3) -ne 'PNG' -or [Text.Encoding]::ASCII.GetString($b,$b.Length-8,4) -ne 'IEND'){throw "PNG invalid $preview"}
 }
 $previewCount+=$previews.Count
 $models+=[pscustomobject][ordered]@{id=$id;title=$row[0].Название_пояснительное;version=$a.version;catalog_id=$a.catalog_id;catalog_grid=$a.catalog_grid;source="Blocks/$id/$id.blend";assembly="Blocks/$id/assembly.json";parts=@($a.instances.part_id|Sort-Object -Unique);instance_count=$a.instances.Count;validation="Blocks/$id/validation.json";checks_passed=$true;game_validation=$false;previews=$previews}
}
$all=@(Get-ChildItem (Join-Path $root Blocks) -Directory|ForEach-Object {$p=Join-Path $_.FullName assembly.json;if(Test-Path $p){Get-Content -Raw $p|ConvertFrom-Json}})
if(@($all|Group-Object catalog_id|Where-Object Count -gt 1).Count){throw 'Duplicate catalog ID'}
$newParts=@(Get-ChildItem (Join-Path $root Parts) -Directory|Where-Object Name -match '^MA-W1[012]-P')
$reused=@($models.parts|Where-Object {$_ -notmatch '^MA-W1[012]-P'}|Sort-Object -Unique)
$instances=($models.instance_count|Measure-Object -Sum).Sum
Save-Crlf (Join-Path $root weapon-continuation2.json) ([ordered]@{schema='MilitaryArmor.WeaponContinuationAuthoringIndex/1';models=$models;new_parts=$newParts.Count;reused_parts=$reused;instances=$instances;previous_source_count=$baseline.Count;existing_sources_unchanged=$true;glb_generated=$false})
$doc="# Лазер, курсовая ракетная установка и самонаводящаяся турель`n`n"
foreach($m in $models){$doc+="- **$($m.id) — $($m.title)**, $($m.catalog_grid -join '×'): [Blender]($($m.source)), [перспектива](Blocks/$($m.id)/Previews/perspective.png), [сверху](Blocks/$($m.id)/Previews/top.png).`n"}
$doc+="`nЛазер читается по оптическому тракту, курсовая ракетная установка — по неподвижной силовой раме, самонаводящаяся турель — по отдельному модулю наведения. Формы и конструкция различаются без опоры на цвет.`n`nНовых деталей: $($newParts.Count); повторно использованные источники: $($reused -join ', '). Экземпляров в трёх сборках: $instances. Планы состава сохранены до моделирования. Новые детали проверены до сборки; независимое открытие исходников проверяет геометрию, материалы, версии, позы и сокеты; функциональные направления и анимации проверены по metadata каждой сборки. Индекс — [weapon-continuation2.json](weapon-continuation2.json), итоговая проверка — [weapon-continuation2-validation.json](weapon-continuation2-validation.json).`n`nПроверены SHA-256 $($baseline.Count) прежних исходников Blender: изменений нет. Всего текущих блоков: $($all.Count). Сцена AllBlocks и папка Renders-45-Top остаются прежним снимком из 58 блоков.`n`nПравая система, +Z вверх, -Y вперёд. BU условные; преобразование игровых pivot в BU и физический масштаб не согласованы. Сетка каталога сохранена в метаданных. Процедурные материалы; файловые текстуры не требуются. Исходники редактируемые, GLB не создавались. Игровая интеграция, LOD, коллайдеры и баланс не входят в эту работу.`n"
Save-Crlf (Join-Path $root WeaponContinuation2.md) $doc
$readme=Join-Path $root README.md;$text=[IO.File]::ReadAllText($readme)
if(-not $text.Contains('(WeaponContinuation2.md)')){Save-Crlf $readme ($text+"`n[Лазер и ракетные установки](WeaponContinuation2.md) — MA-W10, MA-W11, MA-W12; индекс weapon-continuation2.json. Текущих блоков: $($all.Count).`n")}
$texts=@(Get-ChildItem (Join-Path $root Blocks),(Join-Path $root Parts) -Recurse -File|Where-Object {$_.FullName -match 'MA-W1[012]' -and $_.Extension -in @('.json','.md','.py')})
$texts+=@(Get-ChildItem (Join-Path $root Tools) -File|Where-Object Name -match '^(build|verify)_MA_W1[012]\.py$')
foreach($file in $texts){if([IO.File]::ReadAllText($file.FullName) -match '(?<!\r)\n'){throw "CRLF $file"}}
if(@(Get-ChildItem (Join-Path $root Blocks),(Join-Path $root Parts) -Recurse -Filter '*.glb'|Where-Object FullName -match 'MA-W1[012]').Count){throw 'Unexpected GLB'}
Save-Crlf (Join-Path $root weapon-continuation2-validation.json) ([ordered]@{checks_passed=$true;blocks=@($models.id);new_blocks=3;new_parts=$newParts.Count;instances=$instances;catalog_ids_and_grids_match=$true;block_independent_checks_passed=$true;previous_blend_sources_checked=$baseline.Count;previous_sources_unchanged=$true;previews=$previewCount;png_integrity=$true;text_CRLF_checked=$texts.Count;total_current_blocks=$all.Count;glb_generated=$false;game_validation=$false})
$models|Select-Object id,catalog_id,instance_count,checks_passed|Format-Table -AutoSize
