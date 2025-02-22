import { util } from '@aws-appsync/utils';

/**
 * Sends a request to the attached data source
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {*} the request
 */
export function request(ctx) {
    const { userId, payLoad } = ctx.args;
    return {
        operation: 'PutItem',
        key: { id: { S: util.autoId() } }, // Ensure key format matches DynamoDB expectations
        attributeValues: {
            userId: { N: userId },
            createdAt: { S: util.time.nowISO8601() },
            // payLoad: { M: util.dynamodb.toMapValues(payLoad) },
            payLoad: {
                M: {
                    meta: {
                        M: {
                            key1: { "N": payLoad.meta.key1 },
                            key2: { "S": payLoad.meta.key2 },
                        }
                    },
                }
            }
        }
    };
}

/**
 * Returns the resolver result
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {*} the result
 */
export function response(ctx) {
    console.log(ctx);
    return ctx.result;
}
