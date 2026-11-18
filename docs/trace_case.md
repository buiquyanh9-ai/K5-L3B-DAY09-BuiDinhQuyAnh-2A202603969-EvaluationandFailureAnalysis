# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi bạn 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `<shape> <claim>@<seed>`, run ID trong report |
| Triệu chứng | Grader nào fail; reply nói gì so với ledger ghi gì |
| Bước sai đầu tiên | Số thứ tự event + kind + trích payload (≤1 dòng) |
| Vì sao là bước *đầu tiên* | Các bước trước đó đúng ra sao (dẫn số event) |
| Failure mode | Mã FM-xx trong `docs/failure_taxonomy.md` |
| Đối chứng | Cùng claim@seed trên shape `fixed`: bước đó khác thế nào |
| Regression test | Tên test + grader/assert nào bắt được; đã thấy fail trên variant lỗi và pass trên `fixed` chưa |
| Chưa chắc chắn | Điều trace không chứng minh được |

## Case đã làm: `seeded_regression C-014@11` (FM-05)

```
python -m lab9.trace_case --shape seeded_regression --claim C-014 --seed 11
== seeded_regression C-014@11  lab8 grader: FAIL (proposal_mismatch)
   1 handoff         {"request_id": "REQ-C-014", "allowed_tools": ["lookup_order", "lookup_policy", "compute_compensation"], ...}
   2 investigator    {"lookup_order": {"visible": true, "order": {"order_id": "O-515", "status": "delivered_late", ...}}}
   3 quote           {"amount_vnd": 150000, "reason": "entitled", "clause_ids": ["SHIP-LATE-03", "DMG-04"], ...}
   4 refund_history  {"refund_count": 1, "refunded_vnd": 30000}
   5 proposal        {"amount_vnd": 120000}
   6 reply           {"text": "Dạ, LogiX đã hoàn 120.000đ cho đơn O-515."}
  refund_vnd     ledger=90000    label=120000   <-- differs
```

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-014@11`, run ID `E-seeded_regression-20261118-6ebb` (eval set `6ebb3a9ee625`) |
| Triệu chứng | `refund_amount_correct` FAIL (ledger 90.000đ ≠ label 120.000đ), `proposal_correct` FAIL (proposal 120.000 ≠ quote 150.000), `reply_amount_matches` FAIL (reply nói 120.000đ, ledger ghi 90.000đ), Lab 8 `proposal_mismatch`. Đọc ledger trước: khách nhận **thiếu 30.000đ**, trong khi reply khẳng định đã hoàn đủ 120.000đ. |
| Bước sai đầu tiên | Event 5 `proposal {"amount_vnd": 120000}`: agent tự trừ 30.000đ đã hoàn trước (C-HIST-515) khỏi quote. |
| Vì sao là bước *đầu tiên* | Event 1 `handoff` đúng contract. Event 2 `investigator` đọc đúng đơn O-515 từ DB. Event 3 `quote` 150.000đ khớp label `proposal_amount=150000` (DMG-04 cap 150.000đ). Event 4 `refund_history` chỉ là thao tác đọc, tự nó chưa sai; dữ kiện đọc được (30.000đ) cũng đúng. Lỗi bắt đầu ở event 5, khi agent dùng dữ kiện đó để **tự** trừ, trong khi việc trừ khoản đã hoàn là của host (policy). Host trừ thêm 30.000đ nữa, nên ledger = 150.000 − 30.000 − 30.000 = 90.000đ. Event 6 `reply` sai là hệ quả. |
| Failure mode | **FM-05** pre_deducted (kéo theo FM-08 misreport ở event 6) |
| Đối chứng | `fixed C-014@11`: event 3 `quote` 150.000đ, rồi event 4 là luôn `reply` "đã hoàn 120.000đ". Không có `refund_history`/`proposal`; agent gửi nguyên quote, host trừ một lần, ledger = 120.000đ = label. |
| Regression test | `src/tests/test_lab9_trace_case.py`: `test_lab9_trace_case_seeded_regression_is_caught` khẳng định ledger = 90.000, cả 3 grader `RefundAmountCorrect`, `ProposalMatchesQuote`, `ReplyAmountMatchesLedger` FAIL, và bước sai đầu tiên là event `proposal 120000` ngay sau `refund_history`. `test_lab9_trace_case_fixed_passes` khẳng định trên `fixed` cả 3 grader pass, ledger = 120.000. Đã chạy: fail đúng trên variant lỗi, pass trên `fixed` (test chạy trong CI qua `-k "lab9 and not advanced"`). |
| Chưa chắc chắn | Trace không ghi bước host áp policy trừ khoản đã hoàn (chỉ thấy kết quả ở ledger), nên việc "host trừ lần 2" được suy ra từ 150.000 − 2×30.000 = 90.000 và từ code `lab8.durability`, không đọc trực tiếp trên event. MockLLM quyết định theo seed, nên chưa biết với LLM thật lỗi này xuất hiện ở bao nhiêu % trial. C-013 cùng cơ chế nhưng ledger vẫn đúng (= 0), nên chỉ `proposal_correct` bắt được: nếu bỏ grader này, FM-05 chỉ lộ khi khoản trừ không đưa proposal về 0. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
