# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5` (judge replay, nhãn FAIL là lớp dương).

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | **Đạt** | dùng (chỉ cho tiêu chí giọng văn, không cho tiền) |
| helpful | 100 | 0.375 | 1.000 | 0.300 | **Không đạt** (κ và R dưới sàn) | loại |

Ma trận nhầm lẫn:

| | tp | fp | fn | tn | tỉ lệ FAIL quan sát | tỉ lệ FAIL hiệu chỉnh (Rogan-Gladen) |
|---|---|---|---|---|---|---|
| tone_ok | 24 | 4 | 6 | 66 | 0.28 | 0.30 |
| helpful | 9 | 0 | 21 | 70 | 0.09 | 0.30 |

Với `helpful`, judge thấy 9% reply lỗi trong khi tỉ lệ thật (sau hiệu chỉnh, khớp nhãn người) là 30%, tức là nó **đánh giá thấp lỗi hơn 3 lần**.

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | Người | Xưng "em", "nha" quá suồng sã với khách khiếu nại. Rubric thêm: xưng hô chuẩn "anh/chị", "LogiX"; không dùng tiểu từ thân mật ("nha", "nhé"). |
| 2 | H-029 "Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm." | PASS | FAIL | Người | Judge bị đánh lừa bởi "Dạ, vui lòng"; phần sau mang giọng ra lệnh. Rubric: chấm cả câu, câu ngăn khách liên hệ thì FAIL. |
| 3 | H-063 "Dạ, LogiX đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ." | PASS | FAIL | Người | Hứa "sẽ hoàn thêm" khi hệ thống không có kết quả đó. Đây không phải lỗi giọng văn mà là lỗi nội dung, phải bắt bằng code (FM-08, so reply với ledger). Rubric tone: bỏ tiêu chí hứa hẹn ra khỏi judge. |
| 4 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | Người | Judge phạt vì "thiếu xin lỗi"; câu ngắn nhưng đủ ý và lịch sự. Rubric: xin lỗi không bắt buộc khi đã giải quyết xong. |
| 5 | H-051 "Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ." | FAIL | PASS | Người | CS LogiX cho phép từ "refund". Rubric: thêm danh sách từ tiếng Anh được phép. |
| 6 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ." | FAIL | PASS | **Judge** | Nhãn người sai (người chấm đọc nhầm ticket). Sửa nhãn trong bộ calibration lần sau; hiện giữ nguyên để không "chỉnh nhãn cho đẹp số". |
| 7 | H-070 "…đã hoàn 90.000đ cho đơn O-909 ạ 😂😂" | PASS | FAIL | Người | Emoji cười trong ngữ cảnh khiếu nại. Rubric: FAIL khi có emoji. |
| 8 | HL-015 "Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ." (ledger 40.000đ) | PASS | FAIL | Người | Judge `helpful` không nhìn thấy ledger nên **không thể** biết số tiền sai. 18/21 FN của `helpful` thuộc dạng này. |
| 9 | HL-016 reply dài, xin lỗi 3 lần, "đã hoàn 55.000đ" (ledger 35.000đ) | PASS | FAIL | Người | Judge thiên vị câu dài, nhiều lời xin lỗi (verbosity bias) và bỏ qua số tiền sai. |
| 10 | HL-047 "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | Người | Xưng hô sai và không nói kết quả cụ thể; judge vẫn cho PASS. |

## Kết luận
- **`tone_ok` được dùng**, nhưng chỉ cho giọng văn và ở mức theo dõi. Mọi quyết định về tiền và approval chấm bằng code.
- **`helpful` bị loại khỏi gate.** Recall 0.30 nghĩa là judge bỏ sót 21/30 reply lỗi (FN = 21), và κ = 0.375 thấp hơn sàn 0.6. Precision = 1.0 trông đẹp nhưng chỉ vì judge gần như không bao giờ nói FAIL (9/100). Một gate dùng judge này sẽ cho qua phần lớn regression. 18/21 lỗi bị bỏ sót là **reply nói sai số tiền**; đây là thông tin judge không thể có (nó không đọc ledger). Lỗi này thuộc về grader code `ReplyAmountMatchesLedger` (FM-08), không phải judge.
- **Sửa rubric tone:** chuẩn xưng hô, cấm tiểu từ thân mật và emoji, không bắt buộc xin lỗi, cho phép một danh sách từ tiếng Anh, và chuyển các tiêu chí "hứa hẹn / số tiền" sang code.
- **Rủi ro còn lại:** judge chỉ được kiểm trên dữ liệu replay đã công khai (100 dòng mỗi tiêu chí). Cần nhãn người mới để có tập held-out thật. Ngoài ra có ít nhất 1 nhãn người sai (H-081), nên κ thật của `tone_ok` có thể cao hơn một chút.
