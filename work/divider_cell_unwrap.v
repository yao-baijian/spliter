// parameter M means the actual width of divisor
module    divider_cell
    (
      input                     clk,
      input                     rstn,
      input                     en,

      input [3:0]               dividend_de_m1,
      input [2:0]             divisor_m1,
      input [2:0]             merchant_ci_m1 , //上一级输出的商
      input [1:0]           dividend_ci_m1 , //原始除数

      output reg [1:0]      dividend_kp,  //原始被除数信息
      output reg [2:0]        divisor_kp,   //原始除数信息
      output reg                rdy ,
      output reg [2:0]        merchant ,  //运算单元输出商
      output reg [2:0]        remainder   //运算单元输出余数
    );

    reg [3:0]       dividend_de;
    reg [2:0]     divisor;
    reg [2:0]     merchant_ci;
    reg [1:0]   dividend_ci;

    always @(posedge clk) begin
            dividend_de   <= dividend_de_m1 ;
            divisor       <= divisor_m1 ;
            merchant_ci   <= merchant_ci_m1 ;
            dividend_ci   <= dividend_ci_m1 ;
    end 

    always @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            rdy            <= 'b0 ;
            merchant       <= 'b0 ;
            remainder      <= 'b0 ;
            divisor_kp     <= 'b0 ;
            dividend_kp    <= 'b0 ;
        end
        else if (en) begin
            rdy            <= 1'b1 ;
            divisor_kp     <= divisor ;  //原始除数保持不变
            dividend_kp    <= dividend_ci ;  //原始被除数传递
            if (dividend >= {1'b0, divisor}) begin
                merchant    <= (merchant_ci<<1) + 1'b1 ; //商为1
                remainder   <= dividend - {1'b0, divisor} ; //求余
            end
            else begin
                merchant    <= merchant_ci<<1 ;  //商为0
                remainder   <= dividend ;        //余数不变
            end
        end // if (en)
        else begin
            rdy            <= 'b0 ;
            merchant       <= 'b0 ;
            remainder      <= 'b0 ;
            divisor_kp     <= 'b0 ;
            dividend_kp    <= 'b0 ;
        end
    end 

endmodule