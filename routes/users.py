import csv
import io
import os
import shutil
from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from models.users import User
from config import create_db_connection, get_upload_folder
from security import pwd_context


router = APIRouter()


@router.get("/get")
def get_users(
    page: int = Query(default=1, description="Page number", ge=1),
    limit: int = Query(default=5, description="Items per page", le=50),
):
    connection = create_db_connection()
    try:
        if connection.is_connected():
            cursor = connection.cursor()

            offset = (page - 1) * limit
            limit = limit

            query = "SELECT * FROM users LIMIT %s OFFSET %s"
            cursor.execute(query, (limit, offset))

            data = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]

            result = []
            for row in data:
                row_dict = dict(zip(column_names, row))
                user = User(**row_dict)
                result.append(user)
            return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        connection.close()


@router.get("/csv")
def download_users_csv(
    page: int = Query(default=1, description="Page number", ge=1),
    per_page: int = Query(default=10, description="Items per page", le=50),
):
    connection = create_db_connection()
    try:
        if connection.is_connected():
            cursor = connection.cursor()
            offset = (page - 1) * per_page
            limit = per_page
            query = "SELECT * FROM users LIMIT %s OFFSET %s"
            cursor.execute(query, (limit, offset))
            data = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            # Create a CSV in-memory buffer
            output = io.StringIO()
            csv_writer = csv.writer(output)
            # Write the CSV header
            csv_writer.writerow(column_names)
            # Write the data rows
            csv_writer.writerows(data)
            # Prepare the CSV data for download
            output.seek(0)
            csv_data = output.getvalue().encode("utf-8")
            # Set the response headers for CSV download
            headers = {
                "Content-Disposition": f"attachment; filename=users_data_page_{page}.csv",
                "Content-Type": "text/csv",
            }
            return StreamingResponse(io.BytesIO(csv_data), headers=headers)

    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        connection.close()


@router.post("/add")
def add_user(user: User):
    connection = create_db_connection()
    try:
        with connection.cursor() as cursor:
            if user_exist(user):
                raise HTTPException(status_code=400, detail="User already exists")
            else:
                query = """
                INSERT INTO users (name, lastname, birthday, dni,username,password) 
                VALUES (%s, %s, %s, %s,%s,%s);
                """

                encrypted_password = pwd_context.encrypt(user.password)
                cursor.execute(
                    query,
                    (
                        user.name,
                        user.lastname,
                        user.birthday,
                        user.dni,
                        user.username,
                        encrypted_password,
                    ),
                )
                connection.commit()
                return JSONResponse(
                    content={"message": "User added successfully"},
                    status_code=200,
                )
    except HTTPException as he:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        connection.close()


@router.put("/update")
def modify_user(user: User):
    connection = create_db_connection()
    try:
        if user_exist(user):
            with connection.cursor() as cursor:
                # query = """
                #     UPDATE users
                #     SET name = %s, lastname = %s, birthday = %s, dni = %s
                #     WHERE id = %s
                #     """
                query = """
                    UPDATE users 
                    SET name    = %s,
                    lastname    = %s,
                    birthday    = %s,
                    dni         = %s,
                    username    = %s,
                    password    = %s
                    WHERE id    = %s
                    """

                encrypted_password = pwd_context.encrypt(user.password)
                cursor.execute(
                    query,
                    (
                        user.name,
                        user.lastname,
                        user.birthday,
                        user.dni,
                        user.username,
                        encrypted_password,
                        user.id,
                    ),
                )
                connection.commit()

                return JSONResponse(
                    content={"message": "Record updated successfully"},
                    status_code=200,
                )
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException as he:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        connection.close()


@router.delete("/delete")
def remove_user(user: User):
    connection = create_db_connection()
    try:
        if user_exist(user):
            with connection.cursor() as delete_cursor:
                delete_query = "Delete FROM users WHERE id = %s"
                delete_cursor.execute(delete_query, (user.id,))
                connection.commit()

                return JSONResponse(
                    content={
                        "message": str(delete_cursor.rowcount)
                        + " Record Deleted successfully"
                    },
                    status_code=200,
                )
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException as he:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        connection.close()


@router.post("/fileUpload")
async def upload_file(file: UploadFile):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    root_directory = os.path.dirname(current_directory)
    upload_folder = os.path.join(root_directory, get_upload_folder())
    try:
        upload_path = os.path.join(upload_folder, file.filename)
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
            return JSONResponse(
                content={"message": "File uploaded successfully"}, status_code=200
            )
    except HTTPException as he:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


def user_exist(user: User):
    connection = create_db_connection()
    with connection.cursor() as cursor:
        query = """SELECT dni FROM users WHERE dni = %s"""
        cursor.execute(query, (user.dni,))
        result = cursor.fetchone()
        cursor.close()
        return result
