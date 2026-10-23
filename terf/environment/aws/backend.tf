terraform {
  backend "s3" {
    bucket         = "alexyeh-tf-state-aws-793012896705-ap-northeast-1-an"
    key            = "fastapi/aws/terraform.tfstate"
    region         = "ap-northeast-1"

    # ---------------------------------------------------------------------------------
    # To enable State Locking on AWS, first create the DynamoDB table (terraform-locks)
    # and uncomment the following dynamodb_table.
    #----------------------------------------------------------------------------------

    # dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
